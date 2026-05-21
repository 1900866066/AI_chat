import streamlit as st
import os
from openai import OpenAI
# 标题
st.title("ywwのAI-智能伴侣")
#logo
st.logo("./resource/Image_1779353928271_346.jpg")
#设置页面
st.set_page_config(layout="wide",
                   page_icon=":robot_face:",
                   page_title="ywwのAI-智能伴侣",
                   initial_sidebar_state="expanded",
                   menu_items={"About": "基于调用deepseekAPI接口开发的AI智能伴侣\n作者：岳文武\nQQ:1900866066"},
                   )
#副标题
st.subheader("软件の吉祥物")
#聊天背景
st.image("./resource/1779353560318.jpg")
# 调用deepseek官方接口
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")
#系统提示词
system_prompt="你是二次元动漫角色樱岛麻衣"
prompt=st.chat_input("请输入问题：")
#如果输入不为none，则调用接口并且显示结果
if prompt:
    response=client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": f"{prompt}"},
        ],
        stream=False,
    )
    prsponse=response.choices[0].message.content
    st.chat_message("user").write(prompt)
    st.chat_message("assistant").write(prsponse)