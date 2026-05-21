import streamlit as st
import os
from openai import OpenAI
#版本号
version="1.0.0"
# 标题
st.title(f"ywwのAI-智能伴侣 V{version} ")
#logo
st.logo("./resource/Image_1779353928271_346.jpg")
#设置页面
st.set_page_config(layout="wide",
                   page_icon=":robot_face:",
                   page_title="ywwのAI-智能伴侣",
                   initial_sidebar_state="expanded",
                   menu_items={"About": "基于调用deepseekAPI接口开发的AI智能伴侣\n\n作者：岳文武\n\nQQ:1900866066"},
                   )
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
system_prompt="你是二次元动漫角色樱岛麻衣"
prompt=st.chat_input("请输入对话：")
#如果输入不为none，则调用接口并且显示结果
if prompt:
    response=client.chat.completions.create(
        model="deepseek-v4-pro",
        #利用滚雪球式信息叠加，每次调用接口，会自动将上次的回复作为下一次输入实现Ai会话记忆
        messages=[
            {"role": "system", "content": f"{system_prompt}"},
            *st.session_state.messages
        ],
        stream=False,
    )
    prsponse=response.choices[0].message.content
    #添加聊天信息缓存
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": prsponse})
    #输出聊天信息
    st.chat_message("user").write(prompt)
    st.chat_message("assistant").write(prsponse)