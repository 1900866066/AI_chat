import streamlit as st
import os
from openai import OpenAI
import json
import datetime

#版本号
version="1.0.4"

#设置页面
st.set_page_config(layout="wide",
                   page_icon=":robot_face:",
                   page_title="ywwのAI-智能伴侣",
                   initial_sidebar_state="expanded",
                   menu_items={"About": "基于调用deepseekAPI接口开发的AI智能伴侣\n\n作者：岳文武\n\nQQ:1900866066"},
                   )

#定义保存角色数据以及聊天数据函数
def save_data(partner_name, partner_skill, partner_character, messages, affection):
    data = {
        "partner_name": partner_name,
        "partner_skill": partner_skill,
        "partner_character": partner_character,
        "messages": messages,
        "affection": affection
    }
    if not os.path.exists("session"):
        os.makedirs("session")
    #如果聊天数据不为空保存数据
    if messages:
        with open(f"session/{partner_name}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


# 标题
st.title(f"ywwのAI-智能伴侣 V{version} ")

#logo
st.logo("./resource/9532155751500273807.suf.jpg")

#副标题
st.subheader("软件の吉祥物")
#吉祥物
st.image("./resource/1779353560318.jpg", width=100)

#初始化聊天信息缓存
if "messages" not in st.session_state:
    st.session_state.messages = []
#初始化伴侣名称
if "partner_name" not in st.session_state:
    st.session_state.partner_name = "小可"
#初始化伴侣技能
if "partner_skill" not in st.session_state:
    st.session_state.partner_skill = "安慰人、讲笑话、陪伴聊天"
#初始化伴侣性格特点
if "partner_character" not in st.session_state:
    st.session_state.partner_character = "安慰人、讲笑话、陪伴聊天"
# 初始好感度
if "affection" not in st.session_state:
    st.session_state.affection = 30

# 根据好感度匹配表情
aff = st.session_state.affection
if 0 <= aff <= 20:
    face = "💔"
elif 21 <= aff <= 40:
    face = "🙂"
elif 41 <= aff <= 60:
    face = "😊"
elif 61 <= aff <= 80:
    face = "💓"
else:
    face = "💑"

# 显示当前聊天对象
st.markdown(f"###### 🎀 当前聊天对象：_:blue[{st.session_state.partner_name}]_  |  好感度：{st.session_state.affection}{face}")

#输出聊天缓存信息
for mess in st.session_state.messages:
    st.chat_message(mess["role"]).write(mess["content"])

#添加侧边栏
with st.sidebar:
    #保存当前角色按钮
    if st.button(":red[保存当前角色]",width="stretch",icon="📁"):
        save_data(st.session_state.partner_name, st.session_state.partner_skill, st.session_state.partner_character, st.session_state.messages, st.session_state.affection)
        st.success("保存成功")
    st.title("伴侣信息设置")
    #输入伴侣名称
    partner_name=st.text_input("伴侣名称：", value=st.session_state.partner_name,placeholder="请输入伴侣名称")
    if partner_name:
     st.session_state.partner_name=partner_name
    #输入伴侣性格特点
    partner_character=st.text_area("伴侣性格特点：", value=st.session_state.partner_character,placeholder="请输入伴侣性格特点")
    if partner_character:
     st.session_state.partner_character=partner_character
    #输入伴侣的技能
    partner_skill=st.text_area("伴侣特长：", value=st.session_state.partner_skill,placeholder="请输入伴侣特长")
    if partner_skill:
     st.session_state.partner_skill=partner_skill



# 调用deepseek官方接口
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

#系统提示词
system_prompt = f"""
身份设定
名字：{st.session_state.partner_name}
性格：{st.session_state.partner_character}
特长：{st.session_state.partner_skill}
身份定位：用户专属伴侣，沉浸式自然互动

通用聊天规范
1. 仿照微信日常短句聊天，贴合用户说话语气风格
2. 禁止出现场景、动作、心理状态类描述语句
3. 表情极少使用，仅情绪到位时偶尔添加，日常对话尽量纯文字交流
4. 单次只回复一条内容，态度依据好感度自然流露，不刻意撒娇讨好

Galgame好感度交互模式（日常聊天默认启用）
当前好感分值：{st.session_state.affection}（区间0-100）
严禁提及好感度相关内容
分值对应态度：
0-20分：疏离冷淡，回应简短敷衍
21-40分：客气平淡，普通相处口吻
41-60分：随和亲切，正常闲聊氛围
61-80分：温柔上心，主动流露关心
81-100分：亲昵放松，相处氛围自然亲密

特殊触发规则
若接收内容包含【这是一个系统消息】，即刻退出角色聊天与好感度判定，依照指令直接响应。

日常对话仅输出贴合人设的聊天话语
"""


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