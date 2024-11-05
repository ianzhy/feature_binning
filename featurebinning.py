# -*- coding:utf-8 -*-
###
# Project: feature_binning
# Created Date: Friday, October 13th 2023, 2:38:37 pm
# Last Modified: Wed May 29 2024
# Modified By: !an
# Author: !an <ianzy@outlook.com>
###


# from concurrent.futures import thread

# import sys
import os
import pathlib
# import re

import pandas as pd
import numpy as np
import threading
import json
# from contextlib import redirect_stderr,redirect_stdout

from flask import Flask, jsonify, render_template,request
from markupsafe import Markup

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



class BinInfo:
    """
    store bin info for each variable, also provide some basic operations like init, update, serialize, deserialize, sync with bin_cache_file, variable binning, etc.
    """

    def __init__(self,splits=None,value_maps=None,woe_maps=None):
        self.splits = splits or []
        self.value_maps = value_maps or {}
        self.woe_maps = woe_maps
        

    def apply_value_mapping(self,ss):
        ss = ss.copy()

        if "null_map" in self.value_maps:
            ss[np.isnan(ss)] = self.value_maps["null_map"]
        i = 0
        while f"vm_{i}" in self.value_maps:
            left_closed,left,right,right_closed,v = self.value_maps[f"vm_{i}"]
            assert not (left is None and right is None) , "at least one of the two should be set"

            if left is not None:
                if left_closed:
                    mask_left = ss >= left
                else:
                    mask_left = ss > left
            else:
                mask_left = True
            if right is not None:
                if right_closed:
                    mask_right = ss <= right
                else:
                    mask_right = ss < right
            else:
                mask_right = True
            ss[mask_left & mask_right] = v
            i += 1
        return ss


    def cut(self,ss,woe_mapping=False):
        if not self.splits:
            raise Exception("splits not set")
        _min,_max = ss.min(),ss.max()
        ss = self.apply_value_mapping(ss)
        _min,_max = min(ss.min(),_min,min(self.splits)), max(ss.max(),_max,max(self.splits))
        # minimum and maximum is processed to inlude all possible values,
        _min,_max = round(_min-0.001,10),round(_max+0.001,10) 
        # process floating accuracy: 3.3+0.001 = 3.3009999999999997
        bins = [_min, *self.splits, _max]
        categories = pd.cut(ss,bins=bins,right=False) # right=False means left closed 
        codes, intervals =  (categories.cat.codes, categories.cat.categories) if isinstance(categories,pd.Series) else (categories.codes, categories.categories)
        if woe_mapping:
            if self.woe_maps:
                return codes.map(self.woe_maps), intervals
            else:
                raise Exception("woe mapping not set")
        else:
            return codes, intervals


    def statistic(self,var,target,only_return_woe=False):
        '''
        
        '''
        categories,intervals = self.cut(var)
        if not isinstance(target,pd.Series) and not isinstance(var,pd.Series):
            target = pd.Series(target)
        mask = target.isin([0,1])
        stats = target[mask].groupby(categories[mask]).agg(["count","sum"]).reset_index()
        stats.columns = ["bin","nobs","bad"]
        stats["bad_rate"] = stats["bad"]/stats["nobs"]
        stats["good"] = stats["nobs"] - stats["bad"]
        total_bad,total_good = stats["bad"].sum(), stats["good"].sum()
        stats["woe"] = stats.apply(lambda x:np.log(x["bad"]/total_bad + 1e-8)-np.log(x["good"]/total_good + 1e-8),axis=1)   
        if only_return_woe:
            return stats["woe"].to_dict()
        stats["iv"] = stats["woe"]*(stats["bad"]/total_bad-stats["good"]/total_good)
        stats["interval"] = stats["bin"].map(lambda x:str(intervals[x]) if x>=0 else "N/A")
        return stats
        
    @staticmethod    
    def splits_by_qcut(ss,qcut=20,precision=3):
        '''
        precision is used when pd.qcut is called, (which actually is the significant digits of the edge of each bin, usually 3 is enough).
        '''
        # categories, bins = pd.qcut(-ss, qcut,retbins=True,duplicates="drop",precision=self.precision) 
        # bins returned by qcut is not the actual intervals applied for binning, 
        # the acutal intervals is the categories.categories(, which is rounded to precision)
        categories = pd.qcut(-ss, qcut, duplicates="drop",precision=precision) 
        if isinstance(categories,pd.Series):
            splits = [-v.right for v in categories.cat.categories[:-1]][::-1]
        else:
            splits = [-v.right for v in categories.categories[:-1]][::-1]
        return splits


    def set_woe_mapping(self,var,target):
        self.woe_maps = self.statistic(var,target,only_return_woe=True)

    def dump_config(self):
        return {"splits":self.splits,"value_maps":self.value_maps,}
    
    @classmethod
    def load_config(cls,config_dict):
        bin_info = cls(config_dict.get("splits",None),config_dict.get("value_maps",None))
        return bin_info
    
    @classmethod
    def save_to_file(cls,bin_info_map,file):
        bin_info_map_str = {var:bin_info.dump_config() for var,bin_info in bin_info_map.items()}
        with open(file,"w") as f:
            json.dump(bin_info_map_str,f)

    @classmethod
    def load_from_file(cls,file):
        with open(file,"r") as f:
            config_dict = json.load(f)
        bin_info_map = {var:cls.load_config(config) for var,config in config_dict.items()}
        return bin_info_map



class WideTable:
    """
    df: dataframe to be binned, target column named "target" must be included to calculate bad_rate of each bin.
    refs: list of dataframe to be compared with, target column named "target" must be included to calculate bad_rate each bin.
    bin_cache_file: default is "./bin_info.csv", file to store bin info, if not exists, a new one will be created.
    label_mapping: dict, mapping of var name and label. if provided, label will show on web page.
    precision: precision of bin edge, default is 8.
    """
    def __init__(self,df,refs=None,bin_cache_file="./bin_info.json",label_mapping=None,var_list=None):
        if "target" not in df.columns:
            print("target column not found,failed to init WideTable")
            raise

        self.logger = logging.getLogger("werkzeug")
        self.df = df.loc[df["target"].notnull()]
        if os.path.exists(bin_cache_file):
            self.bin_info_dict = BinInfo.load_from_file(bin_cache_file)
            print(f"bin cache file found at {os.path.abspath(bin_cache_file)}")
        else:
            self.bin_info_dict = {}
            print(f"bin cache file not found, a new one will be created at {os.path.abspath(bin_cache_file)}")

        self.refs = refs or []
        self.var_list = var_list
        self.label_mapping = label_mapping or {}


    def var_stat(self,var,splits=None,qcut=None,update_bin=True):
        min_edge,max_edge = self.df[var].replace([np.inf,-np.inf],[np.nan,np.nan]).apply(["min","max"])
        
        if var not in self.bin_info_dict:
            self.bin_info_dict[var] = BinInfo()
            if qcut is None and splits is None:
                self.bin_info_dict[var].splits = BinInfo.splits_by_qcut(self.df[var],qcut=20)
            
        if qcut is not None:
            self.bin_info_dict[var].splits = BinInfo.splits_by_qcut(self.df[var],qcut=qcut)
        elif splits is not None: 
            # TODO: check if all splits is valid
            self.bin_info_dict[var].splits = sorted(splits)
        else:
            pass

        if update_bin:
            BinInfo.save_to_file(self.bin_info_dict,"./bin_info.json")

        stats_list = []        
        for i,idf in enumerate([self.df, *self.refs]):
            stats_list.append(self.bin_info_dict[var].statistic(idf[var],idf["target"]))


        info = {
            "var":var,
            "var_label":self.label_mapping.get(var,""),
            "splits":self.bin_info_dict[var].splits,
            'value_maps':self.bin_info_dict[var].value_maps,
            "max":max_edge,
            "min":min_edge,
            "iv":stats_list[0]["iv"].sum(),
            "total":int(stats_list[0]["nobs"].sum()),
            "refs":[idf.to_dict(orient="records") for idf in stats_list[1:]],    
        }
                
        return stats_list[0].to_dict(orient="records"), info

    def var_binning(self,var_data,var_name,return_woe=False):
        if var_name not in self.bin_info_dict:
            raise Exception(f"{var_name} not in bin_info_dict")
        return self.bin_info_dict[var_name].cut(var_data,woe_mapping=return_woe)

    def run_app(self,*args,**kwargs):
        pkg_dir = pathlib.Path(__file__).absolute().parent
        app = Flask("binning_server",static_folder= pkg_dir / "flask_file", template_folder=pkg_dir / "flask_file",static_url_path="/static")
        app.config["ENV"] = "development"
        app.config["TEMPLATES_AUTO_RELOAD"] = True
       

        @app.route("/",methods=["GET"])
        def index():
            # return jsonify("feture binning server")
            return render_template(
                "index.html",
                data_shape = str(self.df.shape),
                data_description = self.df.describe(include='all').to_html(na_rep=""),
                refs_info = f"{'|'.join([f'{i}: {idf.shape}' for i,idf in enumerate(self.refs)])}",
                var_list = Markup(json.dumps(self.var_list or [var for var in self.df.columns if var not in ["target"] and pd.api.types.is_numeric_dtype(self.df[var])])),
            )


        @app.route("/test",methods=["GET","POST"])
        def test():
            if request.method == "GET":
                var = request.args.get("var")
                qcut = request.args.get("qcut",None)
                if qcut is not None: 
                    stats, info = self.var_stat(var,qcut=int(qcut))
                else:
                    stats, info = self.var_stat(var)
                var_list = self.var_list or [var for var in self.df.columns if var not in ["target"] and pd.api.types.is_numeric_dtype(self.df[var])]
                return render_template(
                    "test.html",
                    # data=Markup({"df":stats,"info":info,"var_list":var_list}), 
                    # None in html caused error, json.dumps will convert None to null
                    data=Markup(json.dumps({"df":stats,"info":info,"var_list":var_list})),
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
        
        @app.route("/update_mapping",methods=["POST"])
        def update_mapping():
            data = json.loads(request.data)
            var = request.args.get("var","")
            self.bin_info_dict[var].value_maps = data
            self.logger.log(logging.DEBUG,data)
            stats,info = self.var_stat(var)
            # print(var,data,self.bin_info_dict[var].value_maps)
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



def single_sample_cut(v,bin_info_config,return_woe=False):
    '''
    return bin code or woe_mapping of a single sample
    bin_info_config: dict, bin_info config of the variable
    '''
    value_maps,splits,woe_maps = bin_info_config["value_maps"],bin_info_config["splits"],bin_info_config["woe_maps"]
    if not splits and not value_maps:
        raise Exception("splits and value_maps not set")

    if value_maps:
        if (v is None or v is np.nan) and  "null_map" in value_maps:
            v = value_maps["null_map"]
        i = 0 
        while f"vm_{i}" in value_maps:
            left_closed,left,right,right_closed,vv = value_maps[f"vm_{i}"]
            if left is not None:
                if left_closed:
                    mask_left = v >= left
                else:
                    mask_left = v > left
            else:
                mask_left = True
            if right is not None:
                if right_closed:
                    mask_right = v <= right
                else:
                    mask_right = v < right
            else:
                mask_right = True
            if mask_left and mask_right:
                v = vv
                # break
            i += 1
    
        if not splits:
            return v

    for i,s in splits:
        if v <= s:
            bin_code = i
            break
    else:
        if v is None or v is np.nan:
            bin_code = -1
        else:
            bin_code = i+1
    
    if return_woe:
        return woe_maps[bin_code]
    else:
        return bin_code


if __name__ == "__main__":


    data1 = pd.read_pickle("./data_sample.pkl")
    data1.shape
    data1.head()
    wt = WideTable(data1)

    t = wt.run_app(port=60006)
    t.join()
  

