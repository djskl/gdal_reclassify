
在Python代码里直接调用processDataset，参数依次为：
- 源文件
- 目标文件
- 源文件中所有的项元值(数组形式，如[1,2,3,4,5])
- 映射规则，x修改为y表示为x:y，多条规则用户逗号连接(如"3:5, 2:6")
- 输出文件中的NODATA
- 输出文件格式
- 压缩方法：'COMPRESS=LZW','COMPRESS=PACKBITS','COMPRESS=DEFLATE' 或 'COMPRESS=JPEG'，参数为数组形式，如['COMPRESS=LZW']


