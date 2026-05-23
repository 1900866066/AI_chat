import streamlit as st
import os
from openai import OpenAI
import json
import datetime

#版本号
version="1.0.5"

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
    #保存角色
    with open(f"session/{partner_name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        st.success("保存成功")

#获取已保存角色名称
def get_partner_names():
    partner_names = []
    if not os.path.exists("session"):
        return partner_names
    for filename in os.listdir("session"):
        if filename.endswith(".json"):
            partner_name = filename[:-5]
            partner_names.append(partner_name)
    return partner_names

#删除角色
def delete_date(name):
    if os.path.exists(f"session/{name}.json"):
        os.remove(f"session/{name}.json")
        st.success("删除成功")
    else:
        st.error("角色不存在")


# 标题
st.title(f"ywwのAI-智能伴侣 V{version} ")

#logo
st.logo("./resource/9532155751500273807.suf.jpg")

#副标题
st.subheader("软件の吉祥物")
#吉祥物
st.image("./resource/Image_1779353928271_346.jpg", width=100)

#先尝试获取角色列表的数据
partner_names = get_partner_names()
#如果存在角色就初始化最后一位角色的聊天数据
if partner_names and "partner_name" not in st.session_state:
    name=partner_names[-1]
    try:
        with open(f"session/{name}.json", "r", encoding="utf-8") as f:
            data=json.load(f)
            st.session_state.partner_name = data["partner_name"]
            st.session_state.partner_skill = data["partner_skill"]
            st.session_state.partner_character = data["partner_character"]
            st.session_state.messages = data["messages"]
            st.session_state.affection = data["affection"]
    except:
        st.session_state.partner_name="小可"


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
    st.session_state.partner_character = "温柔体贴、善解人意"
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

    # 新建角色按钮
    if st.button(":red[新建角色]", width="stretch", icon="🆕"):
        # 初始化新建状态
        st.session_state.creating_new = True

    # 如果处于新建模式，显示输入框
    if st.session_state.get("creating_new", False):
        st.divider()
        st.markdown("**创建新角色**")

        # 使用动态key避免冲突
        if "new_name_counter" not in st.session_state:
            st.session_state.new_name_counter = 0
        #新角色名字
        new_name = st.text_input(
            "新角色名称：",
            key=f"new_partner_name_{st.session_state.new_name_counter}",
            placeholder="请输入名称"
        )
        #新角色性格
        new_character = st.text_area("新角色性格", placeholder="请输入性格特点")
        #新角色特长
        new_skill = st.text_area("新角色特长", placeholder="请输入特长")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 确认创建", width="stretch", key=f"confirm_{st.session_state.new_name_counter}"):
                if not new_name or not new_name.strip():
                    st.error("名称不能为空")
                elif new_name in get_partner_names():
                    st.error(f"角色 '{new_name}' 已存在")
                else:
                    # 先保存当前角色（如果有聊天记录）
                    if st.session_state.messages:
                        save_data(st.session_state.partner_name, st.session_state.partner_skill,
                                  st.session_state.partner_character, st.session_state.messages,
                                  st.session_state.affection)

                    # 创建新角色
                    st.session_state.partner_name = new_name.strip()
                    st.session_state.messages = []
                    st.session_state.affection = 30  # 重置好感度
                    st.session_state.partner_skill=new_skill
                    st.session_state.partner_character=new_character
                    save_data(st.session_state.partner_name, st.session_state.partner_skill,
                              st.session_state.partner_character, st.session_state.messages,
                              st.session_state.affection)

                    # 清理新建状态
                    st.session_state.creating_new = False
                    st.session_state.new_name_counter += 1  # 更新counter避免key冲突

                    st.success(f"角色 '{new_name}' 创建成功！")
                    st.rerun()

        with col2:
            if st.button("❌ 取消", width="stretch", key=f"cancel_{st.session_state.new_name_counter}"):
                # 清理新建状态
                st.session_state.creating_new = False
                st.session_state.new_name_counter += 1  # 更新counter避免key冲突
                st.rerun()

    #渲染角色列表
    partner_names = get_partner_names()
    for name in partner_names:
        col1,col2=st.columns([0.6,0.4])
        with col1:
            if st.button(f"{name}",key=name,width="stretch"):
                #加载角色数据
                with open(f"session/{name}.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                #更新角色数据
                st.session_state.partner_name = data["partner_name"]
                st.session_state.partner_skill = data["partner_skill"]
                st.session_state.partner_character = data["partner_character"]
                st.session_state.messages = data["messages"]
                st.session_state.affection = data["affection"]
                st.rerun()
        with col2:
            if st.button("❌DEL",key=f"session_{name}",width="stretch"):
                delete_data(name)

    st.title("伴侣信息设置")

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