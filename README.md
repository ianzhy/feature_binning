# feature_binning

interactive feature binning tool.

TODO:

* [ ] 页面上显示bin_code, bin_label
* [ ] 增加特殊值处理功能，通过categorical value实现，特殊值直接指定到某个bin_code上
* [ ] 实现类别型变量分箱功能
* [X] 常用版本测试：python==3.6.8, lightGBM==2.2.2, pandas==0.23.0
* [X] 增加对比数据集的展示：支持多个数据集同时展示分箱统计图表
* [ ] 统一通过splits分箱的实现，保证var_stat和var_cut结果一致
* [ ] 统一分bin的precision
