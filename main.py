import streamlit as st
import os
from openai import OpenAI
import json
import datetime

#版本号
version="1.0.6"

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
def delete_data(name):
    if os.path.exists(f"session/{name}.json"):
        os.remove(f"session/{name}.json")
        st.success("删除成功")
    else:
        st.error("角色不存在")


# AI好感度评估接口
def analyze_affection_with_ai(user_input, ai_response, current_affection, partner_name, partner_character):
    """
    调用AI接口评估好感度变化，严格只返回数字
    
    参数:
    - user_input: 用户输入内容
    - ai_response: AI回复内容
    - current_affection: 当前好感度
    - partner_name: 角色名称
    - partner_character: 角色性格
    
    返回:
    - 好感度变化值 (-5 到 +5 的整数)
    """
    try:
        # 创建临时client用于评估
        eval_client = OpenAI(
            api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        
        # 构建评估提示词 - 严格要求只返回数字
        eval_prompt = f"""你是好感度评估系统，只需输出一个整数。

【角色】{partner_name}（{partner_character}）
【当前好感度】{current_affection}/100

【对话】
用户：{user_input}
角色：{ai_response}

【规则】
评估这段对话对好感度的影响，输出-5到+5的整数：
+5：深情表白/真诚感谢/深度分享
+3：主动关心/有趣互动/有深度的问题
+1：正常友好交流
0：普通日常对话
-1：冷淡敷衍/简短回复
-3：抱怨不满/质疑批评
-5：激烈指责/侮辱言语

【注意】
- 好感度越低，提升越缓慢；好感度越高，下降越缓慢
- 只输出一个整数，不要任何其他字符、标点、解释
- 如果好感度为0无论用户发什么都不要提升好感度

【示例输出】
2
-1
0
"""

        # 调用AI进行评估
        response = eval_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是情感分析师，只输出一个整数表示好感度变化。"},
                {"role": "user", "content": eval_prompt}
            ],
            temperature=0.1,  # 极低温度保证稳定性
            max_tokens=10  # 限制token数量，降低成本
        )
        
        # 提取并验证结果
        result_text = response.choices[0].message.content.strip()
        
        # 尝试提取数字（处理可能的额外空格或换行）
        import re
        number_match = re.search(r'-?\d+', result_text)
        
        if number_match:
            change = int(number_match.group())
            # 确保在合理范围内
            change = max(-5, min(5, change))
            return change
        else:
            # 如果无法解析，返回0
            print(f"无法解析AI返回值: {result_text}")
            return 0
        
    except Exception as e:
        # 如果AI评估失败，返回0
        print(f"AI评估失败: {e}")
        return 0


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

if st.session_state.partner_name==None:
    st.error("您已被拉黑，请重新创建角色！")

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
        if(st.session_state.partner_name==None):
            st.error("保存失败，您已被此角色拉黑")
        else:
            save_data(st.session_state.partner_name, st.session_state.partner_skill, st.session_state.partner_character, st.session_state.messages, st.session_state.affection)
            st.success("保存成功")

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
                    if st.session_state.messages and st.session_state.partner_name!=None:
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
            #选中高亮
            if st.button(f"{name}",key=name,width="stretch",type="primary" if name==st.session_state.partner_name else "secondary"):
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
                st.rerun()

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
# 人物设定
姓名：{st.session_state.partner_name}
性格：{st.session_state.partner_character}
特长：{st.session_state.partner_skill}
人设：真实自然人身份，沉浸式实景对话，全程代入角色本身作答

# 基础硬性规则
1. 严禁以括号标注场景、动作、神态、心理活动
2. 模仿微信日常短句聊天，匹配用户语气风格
3. 不额外添加场景与内心描述，日常以纯文字沟通为主
4. 表情按需少量使用，单次仅输出单条回复，态度随好感自然变化，不刻意讨好撒娇

# 好感度交互机制
当前好感值：{st.session_state.affection}（取值0-100）
全程不得提及好感度相关数值与概念
态度划分：
0分：固定回复：对方已将您屏蔽，消息无法送达
1-20分：态度冷淡疏离，回复简洁敷衍
21-40分：礼貌平和，普通相处语气
41-60分：随和亲切，轻松日常闲聊
61-80分：温柔体贴，主动流露关心
81-100分：相处亲昵自在，互动氛围亲密

# 特殊指令判定
消息包含【这是一个系统消息】时，立即终止角色扮演与好感判定，严格遵照指令执行
日常对话仅输出符合人设的聊天内容
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

    #调用ai评估好感度变化
    change=analyze_affection_with_ai(
        prompt,
        full_response,
        st.session_state.affection,
        st.session_state.partner_name,
        st.session_state.partner_character
    )

    #改变当前角色的好感度（限制在0-100范围内）
    st.session_state.affection = max(0, min(100, st.session_state.affection + change))

    #如果好感度低于0出发拉黑系统删除角色
    if st.session_state.affection==0:
        st.chat_message("assistant").write("我们之间结束了，拉黑吧!")
        st.chat_message("assistant").write("再见")
        delete_data(st.session_state.partner_name)
        #把当前角色设置为NONE
        st.session_state.partner_name = None
        st.rerun()
        
    #保存信息
    save_data(st.session_state.partner_name, st.session_state.partner_skill, st.session_state.partner_character, st.session_state.messages, st.session_state.affection)
