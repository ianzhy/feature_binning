# -*- coding:utf-8 -*-
###
# Project: feature_binning
# Created Date: Friday, October 13th 2023, 2:38:37 pm
# Last Modified: Fri Oct 13 2023
# Modified By: !an
# Author: !an <ianzy@outlook.com>
###


import pandas as pd
import numpy as np
import threading
import json
from flask import Flask, jsonify, render_template,request,Markup

class WideTable:
    def __init__(self,df):
        self.df = df
        self.bin_dict = {}

    def var_stat(self,var,splits=None):
        if splits is None: 
            if var not in self.bin_dict:
                categories, bins = pd.qcut(self.df[var], 20, retbins=True,duplicates="drop")
            else:
                bins = self.bin_dict[var]
                categories = pd.cut(self.df[var], bins=bins)
        else:
            bins = [self.df[var].min()-1] + sorted(splits) + [self.df[var].max()+1]
            categories = pd.cut(self.df[var], bins=bins)

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
        info = {
            "var":var,
            "splits":list(categories.cat.categories.left)[1:], # left edge not needed, only the splits
            "max":self.df[var].max(),
            "min":self.df[var].min(),
            "iv":stats["iv"].sum(),
            "total":int(stats["nobs"].sum()),    
        }
                
        return stats, info
    
    def update_bin(self,var,bins):
        self.bin_dict[var] = bins

if __name__ == "__main__":


    data1 = pd.read_pickle("./data_sample.pkl")
    data1.shape
    data1.head()
    wt = WideTable(data1)


    app = Flask("data_server",static_folder="./flask_file",template_folder="./flask_file",static_url_path="/static")

    DATA = {"data1":data1}


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
            stats, info = wt.var_stat(var)
            return render_template(
                "test.html",
                data=Markup({"df":stats.to_dict(orient="records"),"info":info})
            )
        else:
            var = request.args.get("var","")
            splits = json.loads(request.data)
            stats, info = wt.var_stat(var,splits)
            return jsonify({"df":stats.to_dict(orient="records"),"info":info})


    app.config["ENV"] = "development"
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    # t=threading.Thread(target=app.run,kwargs={'port':50000})
    # t.start()
    # print('running')
    app.run(port=50000)


