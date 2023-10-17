# -*- coding:utf-8 -*-
###
# Project: feature_binning
# Created Date: Friday, October 13th 2023, 2:38:37 pm
# Last Modified: Tue Oct 17 2023
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
# from flask_signal import signal



class WideTable:
    def __init__(self,df,bin_cache_file="./bin_info.csv"):
        self.df = df
        if os.path.exists(bin_cache_file):
            self.bin_info = pd.read_csv(bin_cache_file,index_col=0)
        else:
            self.bin_info = pd.DataFrame(columns=range(50))

    def var_stat(self,var,splits=None,qcut=None):
        min_edge,max_edge = self.df[var].replace([np.inf,-np.inf],[np.nan,np.nan]).apply(["min","max"])
        min_edge,max_edge = min_edge-1,max_edge+1
        if qcut is not None:
            categories, bins = pd.qcut(self.df[var], qcut, retbins=True,duplicates="drop")
        elif splits is not None: 
            bins = [min_edge] + sorted(splits) + [max_edge]
            bins = np.unique(bins)
            categories = pd.cut(self.df[var], bins=bins)
        elif var in self.bin_info.index:
            bins = self.bin_info.loc[var].dropna().drop_duplicates().values
            categories = pd.cut(self.df[var], bins=bins)
        else:
            categories, bins = pd.qcut(self.df[var], 20, retbins=True,duplicates="drop")

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
    
    def update_bin(self,var,bins):
        self.bin_info.loc[var] = np.nan
        self.bin_info.loc[var,range(len(bins))] = bins
        
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
                print("splits:\t",splits)
                stats, info = self.var_stat(var,splits)
                print(stats)
                print(info)
                return jsonify({"df":stats.to_dict(orient="records"),"info":info})

        @app.route('/shutdown',methods=['GET'])
        def shutdown():
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()
            return 'Server shutting down...'

        def run_server(*args,**kwargs):
            with redirect_stdout(open("./binning_flask_server.log", "a")), redirect_stderr(sys.stdout):
                app.run(*args,**kwargs)


        t=threading.Thread(target=run_server,kwargs={'port':50000,**kwargs})
        t.setDaemon(True)
        t.start()
        print(f'server running on {kwargs.get("host","127.0.0.1")}:{kwargs.get("port",50000)}')
        # app.run(host="0.0.0.0",port=50000)



if __name__ == "__main__":


    data1 = pd.read_pickle("./data_sample.pkl")
    data1.shape
    data1.head()
    wt = WideTable(data1)


    app = Flask("data_server",static_folder="./flask_file",template_folder="./flask_file",static_url_path="/static")

    DATA = {"data1":data1}

    @app.route("/",methods=["GET"])
    def index():
        return jsonify("feture binning server")

    @app.route("/data_list",methods=["GET"])
    def get_data():
        return jsonify(list(DATA.keys()))

    @app.route("/data_desc/<data_name>",methods=["GET"])
    def get_data_desc(data_name):
        desc = {
            "shape":str(DATA[data_name].shape),
            "columns":str(DATA[data_name].columns),
            "indexs":str(DATA[data_name].index),
        }
        return jsonify(desc)

    @app.route("/data1/<ind>/<col>",methods=["GET"])
    def get_data_by_key(ind,col):
        return jsonify(str(DATA['data1'].loc[ind,col]))

    @app.route("/data_set/<key>/<value>",methods=["GET"])
    def set_data_by_key(key,value):
        DATA[key] = value
        return jsonify("ok")

    @app.route("/test",methods=["GET","POST"])
    def test():
        if request.method == "GET":
            var = request.args.get("var")
            qcut = request.args.get("qcut",None)
            if qcut is not None: 
                stats, info = wt.var_stat(var,qcut=int(qcut))
            else:
                stats, info = wt.var_stat(var)
            return render_template(
                "test.html",
                data=Markup({"df":stats.to_dict(orient="records"),"info":info})
            )
        else:
            var = request.args.get("var","")
            splits = json.loads(request.data)
            stats, info = wt.var_stat(var,splits)
            print(stats,info)
            return jsonify({"df":stats.to_dict(orient="records"),"info":info})

    @app.route("/cut",methods=["POST"])
    def data_cut():
        var = request.args.get("var")
        splits = json.loads(request.data)
        if isinstance(splits,int):
            stats, info = wt.var_stat(var,qcut=splits)
        else:
            stats, info = wt.var_stat(var,splits=splits)
        return jsonify({"df":stats.to_dict(orient="records"),"info":info})



    app.config["ENV"] = "development"
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    # t=threading.Thread(target=app.run,kwargs={'port':50000})
    # t.start()
    # print('running')
    app.run(host="0.0.0.0",port=50000)


