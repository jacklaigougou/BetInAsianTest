
name : 项目流程说明
description : 本项目是一个套利项目的执行器,dispatch接收命令,执行相应的操作

#
项目通过ws服务器与dispatch端进行沟通,通过dispatch发送的不同命令,automation则进行不同的处理.

## 
application\application.py 文件用于构造异步任务,并路由到对应的处理方法.

##
application\handlers\dispatch_handler.py 文件中最重要的几个处理分别是
case 'onlineAccount' 用于初始化和构造handler对象.
case 'new_order' 在接受到新的订单时进行盘口和赔率的查询
case 'betting_order' | 'betting'  在接受下单命令之后进行下单操作.

