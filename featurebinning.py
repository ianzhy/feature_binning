# -*- coding:utf-8 -*-
###
# Project: feature_binning
# Created Date: Friday, October 13th 2023, 2:38:37 pm
# Last Modified: Tue Nov 21 2023
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
    def __init__(self,df,refs=None,bin_cache_file="./bin_info.csv",label_mapping=None):
        if "target" not in df.columns:
            print("target column not found,failed to init WideTable")
            raise

        self.logger = logging.getLogger("werkzeug")
        self.df = df.loc[df["target"].notnull()]
        if os.path.exists(bin_cache_file):
            self.bin_info = pd.read_csv(bin_cache_file,index_col=0)
        else:
            print("bin cache file not found, create a new one")
            self.bin_info = pd.DataFrame(columns=range(50))
            self.bin_info.to_csv("./bin_info.csv")

        self.refs = refs or []
        self.label_mapping = label_mapping or {}


    def var_stat(self,var,splits=None,qcut=None,update_bin=True):
        min_edge,max_edge = self.df[var].replace([np.inf,-np.inf],[np.nan,np.nan]).apply(["min","max"])
        if qcut is not None:
            categories, bins = pd.qcut(self.df[var], qcut,retbins=True,duplicates="drop")
        elif splits is not None: 
            # TODO: check if all splits is valid
            bins = [min_edge-0.001] + sorted(splits) + [max_edge+0.001]
            bins = np.unique(bins)
            categories = pd.cut(self.df[var], bins=bins,include_lowest=True)
        elif var in self.bin_info.index:
            bins = self.bin_info.loc[var].dropna().drop_duplicates().values
            bins[0] = min(self.df[var].min()-0.001,bins[0])   # 调整下上下限
            bins[-1] = max(self.df[var].max()+0.001,bins[-1])
            categories = pd.cut(self.df[var], bins=bins,include_lowest=True)
        else:
            categories, bins = pd.qcut(self.df[var], 20, retbins=True,duplicates="drop")

        if update_bin:
            self.update_bin(var,bins)

        stats_list = []        
        for i,idf in enumerate([self.df, *self.refs]):
            categories = pd.cut(idf[var], bins=bins,include_lowest=True)
            stats = idf.groupby(categories.cat.codes).agg({"target":[
                "count",                # number of observations
                "mean",                 # bad_rate
                ("bad",lambda x:(x==1).sum()),  # number of bads
                ("good",lambda x:(x==0).sum()),  # number of goods
            ]})
            stats = stats.reset_index()
            stats.columns = ["bin","nobs","bad_rate","bad","good"]
            total_bad,total_good = stats["bad"].sum(), stats["good"].sum()
            stats["woe"] = stats.apply(lambda x:np.log((x["bad"]+1)/total_bad)-np.log((x["good"]+1)/total_good),axis=1)
            stats["iv"] = stats["woe"]*(stats["bad"]/total_bad-stats["good"]/total_good)
            
            stats["interval"] = stats["bin"].map(lambda x:str(categories.cat.categories[x]) if x>=0 else "N/A") 
            stats_list.append(stats)
            if i==0:
                splits = list(categories.cat.categories.right)[:-1]
                # if splits[0] < min_edge: splits[0] = min_edge
                # if splits[-1] > max_edge: splits[-1] = max_edge

        info = {
            "var":var,
            "var_label":self.label_mapping.get(var,""),
            "splits":splits, # left edge not needed, only the splits
            "max":max_edge,
            "min":min_edge,
            "iv":stats_list[0]["iv"].sum(),
            "total":int(stats_list[0]["nobs"].sum()),
            "refs":[idf.to_dict(orient="records") for idf in stats_list[1:]],    
        }
                
        return stats_list[0].to_dict(orient="records"), info

    def var_cut(self,data,var,calculate_woe=True):
        if var not in self.bin_info.index:
            raise Exception(f"{var} not in bin_info")
        bins = self.bin_info.loc[var].dropna().drop_duplicates().values
        bins[0] = round(min(data[var].min()-0.001,bins[0]),8)   # 调整下上下限
        bins[-1] = round(max(data[var].max()+0.001,bins[-1]),8)
        categories = pd.cut(data[var],bins,include_lowest=True)
        var_bin = categories.cat.codes
        bin_labels = {i:label for i,label in enumerate(categories.cat.categories.astype(str))}
        if calculate_woe:
            if "target" not in data.columns:
                raise Exception("target column not found, can't calculate woe")
            count = data.groupby(var_bin).agg({"target":[
                "count",                # number of observations
                # "mean",                 # bad_rate
                ("bad",lambda x:(x==1).sum()),  # number of bads
                ("good",lambda x:(x==0).sum()),  # number of goods
            ]})
            count.columns = "total,bad,good".split(",")
            rate = count/count.sum()
            woe = np.log((rate["bad"]+0.001)/(rate["good"]+0.001))
            small_bin = rate["total"]<0.005
            if small_bin.any():
                print(f"{var}: woes set to zero for very small bins")
                print(count.loc[small_bin])
            woe.loc[small_bin] = 0
            woe_bin_mapping = woe.to_dict()
            var_woe = pd.Series(woe.loc[var_bin.values].values,index=data.index)
            return var_bin,bin_labels,var_woe,woe_bin_mapping
        else:
            return var_bin,bin_labels



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
                    data=Markup({"df":stats,"info":info})
                )
            else:
                var = request.args.get("var","")
                splits = json.loads(request.data)
                self.logger.log(logging.DEBUG,"splits:\t"+str(splits))
                stats, info = self.var_stat(var,splits)
                self.logger.log(logging.DEBUG,stats)
                self.logger.log(logging.DEBUG,info)
                return jsonify({"df":stats,"info":info})

        @app.route("/qcut",methods=["POST"])
        def var_qcut():
            var = request.args.get("var","")
            data = json.loads(request.data)
            qcut = int(data.get("qcut_num"))
            stats, info = self.var_stat(var,qcut=qcut)
            return jsonify({"df":stats,"info":info})


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
        return t
        # app.run(host="0.0.0.0",port=50000)



if __name__ == "__main__":


    data1 = pd.read_pickle("./data_sample.pkl")
    data1.shape
    data1.head()
    wt = WideTable(data1)

    t = wt.run_app(port=60006)
    t.join()
  

