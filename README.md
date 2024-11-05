# feature_binning

interactive feature binning tool.

支持可视化可交互的特征分箱过程

TODO:

* [ ] 页面上显示bin_code, bin_label
* [X] 增加特殊值处理功能，通过值映射实现
* [ ] 实现类别型变量分箱功能
* [X] 常用版本测试：python==3.6.8, lightGBM==2.2.2, pandas==0.23.0
* [X] 增加对比数据集的展示：支持多个数据集同时展示分箱统计图表
* [X] 功能实现：优化页面展示，支持传入中文标签
* [X] 功能实现：支持页面输入变量跳转
* [X] 统一通过splits分箱的实现，保证var_stat和var_cut结果一致
* [X] 统一分bin的precision
* [X] 改为默认左闭右开
* [X] bug fix：鼠标float在切分点时，ref图像中关联的bar没有高亮
