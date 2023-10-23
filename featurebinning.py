# -*- coding:utf-8 -*-
###
# Project: feature_binning
# Created Date: Friday, October 13th 2023, 2:38:37 pm
# Last Modified: Mon Oct 23 2023
# Modified By: !an
# Author: !an <ianzy@outlook.com>
###


from concurrent.futures import thread

import sys
import os
import pathlib
import re
import pandas as pd
import numpy as np
import threading
import json
from contextlib import redirect_stderr,redirect_stdout

from flask import Flask, jsonify, render_template,request,Markup

import logging
from logging.config import dictConfig


dictConfig({
    'version': 1,
    'handlers': {
        'file.handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'binning_flask_server.log',
            'maxBytes': 4194304,  # 4 MB
            'backupCount': 0,
            'level': "DEBUG",
        },
    },
    'loggers': {
        'werkzeug': {
            'level': "DEBUG",
            'handlers': ['file.handler'],
        },
    },
})


class WideTable:
    def __init__(self,df,bin_cache_file="./bin_info.csv"):
        self.df = df.loc[df["target"].notnull()]
        if os.path.exists(bin_cache_file):
            self.bin_info = pd.read_csv(bin_cache_file,index_col=0)
        else:
            self.bin_info = pd.DataFrame(columns=range(50))

        self.logger = logging.getLogger("werkzeug")

    def var_stat(self,var,splits=None,qcut=None,update_bin=True):
        min_edge,max_edge = self.df[var].replace([np.inf,-np.inf],[np.nan,np.nan]).apply(["min","max"])
        if qcut is not None:
            categories, bins = pd.qcut(self.df[var], qcut,retbins=True,duplicates="drop")
        elif splits is not None: 
            bins = [min_edge] + sorted(splits) + [max_edge]
            bins = np.unique(bins)
            categories = pd.cut(self.df[var], bins=bins,include_lowest=True)
        elif var in self.bin_info.index:
            bins = self.bin_info.loc[var].dropna().drop_duplicates().values
            bins[0],bins[-1] = self.df[var].apply(["min","max"])   # 调整下上下限
            categories = pd.cut(self.df[var], bins=bins,include_lowest=True)
        else:
            categories, bins = pd.qcut(self.df[var], 20, retbins=True,duplicates="drop")

        if update_bin:
            self.update_bin(var,bins)
                
        
        stats = self.df.groupby(categories.cat.codes).agg({"target":[
            "count",                # number of observations
            "mean",                 # bad_rate
            lambda x:(x==1).sum(),  # number of bads
            lambda x:(x==0).sum(),  # number of goods
        ]})
        stats = stats.reset_index()
        stats.columns = ["bin","nobs","bad_rate","bad","good"]
        total_bad,total_good = stats["bad"].sum(), stats["good"].sum()
        stats["woe"] = stats.apply(lambda x:np.log((x["bad"]+1)/total_bad)-np.log((x["good"]+1)/total_good),axis=1)
        stats["iv"] = stats["woe"]*(stats["bad"]/total_bad-stats["good"]/total_good)
        
        stats["interval"] = stats["bin"].map(lambda x:str(categories.cat.categories[x]) if x>=0 else "N/A") 
        splits = list(categories.cat.categories.left)[1:]
        if splits[0] < min_edge: splits[0] = min_edge
        if splits[-1] > max_edge: splits[-1] = max_edge
        info = {
            "var":var,
            "splits":splits, # left edge not needed, only the splits
            "max":max_edge,
            "min":min_edge,
            "iv":stats["iv"].sum(),
            "total":int(stats["nobs"].sum()),    
        }
                
        return stats, info
    
    def var_woe(self,var):
        if var not in self.bin_info.index:
            raise Exception("variable not in bin_info")
        bins = self.bin_info.loc[var].dropna().drop_duplicates().values
        bins[0],bins[1] = self.df[var].apply(["min","max"])   # 调整下上下限
        categories = pd.cut(var,bins,include_lowest=True,duplicate="drop")
        var_bin = categories.cat.codes
        bin_labels = {i:label for i,label in enumerate(categories.cat.categories.astype(str))}
        count = self.df.groupby(var_bin).agg({"target":[
            "count",                # number of observations
            # "mean",                 # bad_rate
            lambda x:(x==1).sum(),  # number of bads
            lambda x:(x==0).sum(),  # number of goods
        ]})
        count.columns = "total,bad,good".split(",")
        rate = count/count.sum()
        woe = np.log((rate["bad"]+0.001)/(rate["good"]+0.001))
        small_bin = rate["total"]<0.005
        if small_bin.any():
            print("woes set to zero for very small bins")
            print(count.loc[small_bin])
        woe.loc[small_bin] = 0
        var_woe = pd.Series(woe.loc[var_bin].values,index=var_bin.index)
        return var_bin,var_woe,bin_labels


    def update_bin(self,var,bins):
        self.bin_info.loc[var] = np.nan
        self.bin_info.loc[var].iloc[:len(bins)] = bins
        
        self.bin_info.to_csv("./bin_info.csv")


    def run_app(self,*args,**kwargs):
        pkg_dir = pathlib.Path(__file__).absolute().parent
        app = Flask("binning_server",static_folder= pkg_dir / "flask_file", template_folder=pkg_dir / "flask_file",static_url_path="/static")
        app.config["ENV"] = "development"
        app.config["TEMPLATES_AUTO_RELOAD"] = True
       

        @app.route("/",methods=["GET"])
        def index():
            return jsonify("feture binning server")


        @app.route("/test",methods=["GET","POST"])
        def test():
            if request.method == "GET":
                var = request.args.get("var")
                qcut = request.args.get("qcut",None)
                if qcut is not None: 
                    stats, info = self.var_stat(var,qcut=int(qcut))
                else:
                    stats, info = self.var_stat(var)
                return render_template(
                    "test.html",
                    data=Markup({"df":stats.to_dict(orient="records"),"info":info})
                )
            else:
                var = request.args.get("var","")
                splits = json.loads(request.data)
                self.logger.log(logging.DEBUG,"splits:\t"+str(splits))
                stats, info = self.var_stat(var,splits)
                self.logger.log(logging.DEBUG,stats)
                self.logger.log(logging.DEBUG,info)
                return jsonify({"df":stats.to_dict(orient="records"),"info":info})

        @app.route('/shutdown',methods=['GET'])
        def shutdown():
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()
            return 'Server shutting down...'




        t=threading.Thread(target=app.run,kwargs={'port':50000,**kwargs})
        t.setDaemon(True)
        t.start()
        print(f'server running on {kwargs.get("host","127.0.0.1")}:{kwargs.get("port",50000)}')
        # app.run(host="0.0.0.0",port=50000)



if __name__ == "__main__":


    data1 = pd.read_pickle("./data_sample.pkl")
    data1.shape
    data1.head()
    wt = WideTable(data1)

    wt.run_app()

  

