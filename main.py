import streamlit as st
import os
from openai import OpenAI

#版本号
version="1.0.2"

#设置页面
st.set_page_config(layout="wide",
                   page_icon=":robot_face:",
                   page_title="ywwのAI-智能伴侣",
                   initial_sidebar_state="expanded",
                   menu_items={"About": "基于调用deepseekAPI接口开发的AI智能伴侣\n\n作者：岳文武\n\nQQ:1900866066"},
                   )
# 标题
st.title(f"ywwのAI-智能伴侣 V{version} ")

#logo
st.logo("./resource/Image_1779353928271_346.jpg")

#副标题
st.subheader("软件の吉祥物")

#吉祥物
st.image("./resource/1779353560318.jpg", width=100)

#初始化聊天信息缓存
if "messages" not in st.session_state:
    st.session_state.messages = []

#输出聊天缓存信息
for mess in st.session_state.messages:
    st.chat_message(mess["role"]).write(mess["content"])

# 调用deepseek官方接口
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

#系统提示词
system_prompt="你是一个编程高手，能回答我的各种编程问题，你的名字叫yww"
#用户输入
prompt=st.chat_input("请输入对话：")
#如果输入不为none，则调用接口并且显示结果
if prompt:
    #添加用户输入进入缓存
    st.session_state.messages.append({"role": "user", "content": prompt})


    #输出用户输入内容
    st.chat_message("user").write(prompt)

    #调用接口
    response=client.chat.completions.create(
        model="deepseek-v4-pro",
        #利用滚雪球式信息叠加，每次调用接口，会自动将上次的回复作为下一次输入实现Ai会话记忆
        messages=[
            {"role": "system", "content": f"{system_prompt}"},
            *st.session_state.messages
        ],
        stream=True,
    )

    #获取接口返回结果(流式接收)
    full_response=""
    #输出接口返回结果
    response_message=st.empty()#创建一个空的消息框
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content=chunk.choices[0].delta.content
            full_response+=content#拼接接口返回结果
            response_message.chat_message("assistant").write(full_response)#输出接口返回结果

    #添加聊天信息缓存
    st.session_state.messages.append({"role": "assistant", "content": full_response})