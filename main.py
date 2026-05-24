import streamlit as st
import os
from openai import OpenAI
import json
import datetime

#版本号
version="1.0.8"

#设置页面
st.set_page_config(layout="wide",
                   page_icon=":robot_face:",
                   page_title="ywwのAI-智能伴侣",
                   initial_sidebar_state="expanded",
                   menu_items={"About": "基于调用deepseekAPI接口开发的AI智能伴侣\n\n作者：岳文武\n\nQQ:1900866066"},
                   )

#尝试从系统环境变量中调取ai_api_key
try:
    ai_api_key=os.environ.get('DEEPSEEK_API_KEY')
except:
    st.error("请设置DEEPSEEK_API_KEY环境变量")

#调用部署本地大模型
#本地大模型名字
LLM_name1="deepseek-r1:8b"
#本地大模型url
LLM_url1="http://localhost:11434/v1"
#api调用官方大模型
#api官方大模型名字
LLM_name2="deepseek-v4-pro"
#api官方大模型url
LLM_url2="https://api.deepseek.com"


#定义保存角色数据以及聊天数据函数
def save_data(partner_name, partner_skill, partner_character, messages, affection):
    if partner_name is None:
        return
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
    try:
        if os.path.exists(f"session/{name}.json"):
            os.remove(f"session/{name}.json")
            st.success("删除成功")
        else:
            st.error("角色不存在")
    except:
        st.error("删除失败")

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
    global option
    try:
        # 创建临时client用于评估
        eval_client = OpenAI(
            api_key=ai_api_key if ai_api_key else "ollama",
            base_url=LLM_url1 if option=="本地部署" else LLM_url2,
        )
        
        # 根据模型类型选择提示词
        if option == "本地部署":
            # 【方案1】极简提示词 - 适配8B小模型
            user_short = user_input[:50] if len(user_input) > 50 else user_input
            ai_short = ai_response[:50] if len(ai_response) > 50 else ai_response
            
            eval_prompt = f"""对话评分(-5到5):
用户:{user_short}
AI:{ai_short}
当前好感:{current_affection}

评分:
5=告白 3=关怀 1=友好 0=普通 -1=冷淡 -3=不满 -5=攻击
只输出一个数字:"""
            
            system_msg = "只输出-5到5之间的一个整数"
            max_tokens = 10  # 增加到10，给本地模型足够空间
            timeout = 15
            print(f"[好感度评估] 📱 使用本地模型(极简提示词)")
        else:
            # 【方案2】完整提示词 - 适配API大模型
            eval_prompt = f"""#角色信息
姓名:{partner_name}|性格:{partner_character}|当前好感:{current_affection}

#本轮对话
用户:{user_input}
AI:{ai_response}

#评分标准(-5~+5)
+5:用户表达爱意/深情告白/重要承诺,且AI情感共鸣强烈
+3:用户暖心关怀/深度互动/主动示好,AI积极回应
+1:用户友好沟通/正常聊天,AI正常回应
 0:平淡日常,无明显情感波动
-1:用户冷淡敷衍/态度消极
-3:用户不满质疑/冷淡疏远
-5:用户言语攻击/侮辱指责

#性格加成规则
IF 角色性格含"温柔/甜美/感性/容易感动":
  - 用户温柔互动→加分上浮(+1→+3,+3→+5)
  - AI展现感动/害羞/开心→额外+1
IF 角色性格含"高冷/傲娇/理性":
  - 用户温柔互动→正常评分
  - AI展现感动→不额外加分

#好感度调节
好感<30→加分降档(+5→+3,+3→+1,+1→0)
好感>70→扣分降档(-5→-3,-3→-1,-1→0)
好感=0→输出0

#输出要求
只输出整数(-5,-3,-1,0,1,3,5),无其他字符"""
            
            system_msg = "你是情感分析师。直接输出一个整数(-5到5)，不要思考过程，只要数字。"
            max_tokens = 50  # 大幅增加，确保模型能输出完整答案
            timeout = 30
            print(f"[好感度评估] ☁️ 使用API模型(完整提示词)")
        
        # 调用AI进行评估
        print(f"[好感度评估] 正在调用API...")
        print(f"[好感度评估] 模型: {LLM_name1 if option=='本地部署' else LLM_name2}")
        print(f"[好感度评估] API Key: {'已设置' if ai_api_key else '未设置'}")
        
        response = eval_client.chat.completions.create(
            model=LLM_name1 if option=="本地部署" else LLM_name2,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": eval_prompt}
            ],
            temperature=0.1,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
        # 调试：打印完整响应结构
        print(f"[好感度评估] 响应对象: {response}")
        print(f"[好感度评估] Choices数量: {len(response.choices) if response.choices else 0}")
        
        # 提取并验证结果
        if not response.choices:
            print(f"[好感度评估] ❌ response.choices为空列表")
            return _simple_affection_eval(user_input, ai_response, current_affection)
            
        if not response.choices[0].message:
            print(f"[好感度评估] ❌ response.choices[0].message为空")
            return _simple_affection_eval(user_input, ai_response, current_affection)
            
        if not response.choices[0].message.content:
            print(f"[好感度评估] ❌ content为空，尝试从reasoning字段提取...")
            
            # 尝试从reasoning_content或reasoning中提取（DeepSeek特有）
            reasoning_text = None
            if hasattr(response.choices[0].message, 'reasoning_content') and response.choices[0].message.reasoning_content:
                reasoning_text = response.choices[0].message.reasoning_content
                print(f"[好感度评估] 找到reasoning_content: '{reasoning_text[:50]}...'")
            elif hasattr(response.choices[0].message, 'reasoning') and response.choices[0].message.reasoning:
                reasoning_text = response.choices[0].message.reasoning
                print(f"[好感度评估] 找到reasoning: '{reasoning_text[:50]}...'")
            
            if reasoning_text:
                import re
                number_match = re.search(r'-?\d+', reasoning_text)
                if number_match:
                    change = int(number_match.group())
                    change = max(-5, min(5, change))
                    print(f"[好感度评估] ✅ 从reasoning提取成功: 变化值={change}")
                    return change
                else:
                    print(f"[好感度评估] ❌ reasoning中未找到数字")
            
            print(f"[好感度评估] 切换到规则评估")
            return _simple_affection_eval(user_input, ai_response, current_affection)
            
        result_text = response.choices[0].message.content.strip()
        
        # 调试输出
        print(f"[好感度评估] AI原始返回: '{result_text}' (长度:{len(result_text)})")
        
        # 如果返回为空，使用规则评估
        if not result_text:
            print(f"[好感度评估] AI返回为空，切换到规则评估...")
            return _simple_affection_eval(user_input, ai_response, current_affection)
        
        # 尝试提取数字
        import re
        number_match = re.search(r'-?\d+', result_text)
        
        if number_match:
            change = int(number_match.group())
            change = max(-5, min(5, change))
            print(f"[好感度评估] ✅ 解析成功: 变化值={change}")
            return change
        else:
            print(f"[好感度评估] ❌ 解析失败: '{result_text}'，使用规则评估")
            return _simple_affection_eval(user_input, ai_response, current_affection)
        
    except Exception as e:
        print(f"[好感度评估] ⚠️ 异常: {type(e).__name__}: {e}")
        # 发生异常时使用简单规则评估
        return _simple_affection_eval(user_input, ai_response, current_affection)


def _simple_affection_eval(user_input, ai_response, current_affection):
    """
    简单的基于规则的评估（备用方案）
    当AI评估失败时使用
    """
    # 合并文本进行分析
    text = (user_input + " " + ai_response).lower()
    
    # 积极词汇
    positive_words = ['爱', '喜欢', '想', '谢谢', '感谢', '好', '开心', '快乐', '幸福', '温暖', '关心', '陪伴', '温柔', '美', '棒', '赞']
    # 消极词汇
    negative_words = ['讨厌', '恨', '烦', '滚', '闭嘴', '垃圾', '废物', '傻', '丑', '无聊', '没用']
    
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    # 计算变化值
    if pos_count >= 3:
        change = 3
    elif pos_count >= 1:
        change = 1
    elif neg_count >= 2:
        change = -3
    elif neg_count >= 1:
        change = -1
    else:
        change = 0
    
    # 好感度调节
    if current_affection < 30 and change > 0:
        change = max(0, change - 1)  # 低好感时加分减少
    elif current_affection > 70 and change < 0:
        change = min(0, change + 1)  # 高好感时扣分减少
    
    print(f"[好感度评估] 🔄 使用规则评估: 积极词{pos_count}个, 消极词{neg_count}个, 变化值={change}")
    return change


# 标题
st.title(f"✨ ywwのAI-智能伴侣 V{version} ✨")


#选择本地大模型还是api官方大模型
option=st.selectbox("选择大模型：", ["本地部署", "api官方大模型"])


#点击下载帮助文档
try:
    st.sidebar.markdown("[点击下载帮助文档](https://github.com/1900866066/AI_chat/blob/main/AI伴侣_帮助文档.docx)")
except:
    pass

#api_key调用失败，让用户手动输入api_key
if not ai_api_key:
    ai_api_key = st.text_input("请输入api_key：", type="password")
    if not ai_api_key:
        st.warning("请输入 DeepSeek API Key 或设置 DEEPSEEK_API_KEY 环境变量")

# 美化CSS样式
st.markdown("""
<style>
/* 全局样式优化 */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 主内容区域背景 - 纯白色 */
.block-container {
    background: #fffff !important;
    border-radius: 20px !important;
    margin-top: 1rem;
    padding: 2rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

/* 主标题 - 白色背景黑色文字 */
h1 {
    text-align: center;
    color: #000000 !important;
    font-weight: 800;
    margin-bottom: 1.5rem;
    font-size: 2rem !important;
    background: rgba(255, 255, 0, 0.9) !important;
    padding: 1rem 2rem;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

h2, h3, h4, h5, h6 {
    color: #000000 !important;
    font-weight: 700 !important;
}

/* 所有段落文字 - 深黑色 */
.stMarkdown p,
.stMarkdown div,
p, 
div[data-testid="stText"] {
    color: #0d1117 !important;
}

/* 聊天对象信息卡片 */
.partner-info {
    background: #f6f8fa;
    padding: 1.2rem 1.5rem;
    border-radius: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin: 1.5rem 0;
    text-align: center;
    font-size: 1.1rem;
    color: #0d1117;
    font-weight: 600;
    border: 2px solid #e1e4e8;
}

/* 好感度数字 - 红色 */
.partner-info span {
    color: #dc3545 !important;
    font-size: 1.3rem;
    font-weight: 700;
}

/* 侧边栏美化 */
.css-1d391kg {
    background: linear-gradient(180deg, #2d2d3a 0%, #1a1a2e 100%) !important;
}

/* 按钮美化 */
.stButton>button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

.stButton>button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
}

/* 输入框美化 */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea {
    border-radius: 10px !important;
    border: 2px solid #d0d7de !important;
    transition: all 0.3s ease !important;
    background: #ffffff !important;
    color: #0d1117 !important;
    font-weight: 500 !important;
}

.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
}

/* 聊天消息美化 - 高对比度 */
.stChatMessage {
    background: #ffffff !important;
    border-radius: 15px !important;
    margin: 0.8rem 0 !important;
    padding: 1.2rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    border: 1px solid #e1e4e8 !important;
}

/* 聊天消息文字颜色 - 深黑色 */
.stChatMessage p, 
.stChatMessage div,
.stChatMessage span {
    color: #0d1117 !important;
    font-size: 1rem !important;
    line-height: 1.7 !important;
    font-weight: 500 !important;
}

/* 用户消息特殊样式 */
.stChatMessage[data-testid="stChatMessageUser"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
}

.stChatMessage[data-testid="stChatMessageUser"] p,
.stChatMessage[data-testid="stChatMessageUser"] div,
.stChatMessage[data-testid="stChatMessageUser"] span {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* AI助手消息特殊样式 */
.stChatMessage[data-testid="stChatMessageAssistant"] {
    background: #f6f8fa !important;
    border: 1px solid #e1e4e8 !important;
}





.mascot-section p,
.mascot-section div {
    color: #0d1117 !important;
}

/* 分隔线美化 */
hr {
    border-color: #e1e4e8 !important;
    margin: 1.5rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

#logo
try:
    st.logo("./resource/9532155751500273807.suf.jpg")
except:
    st.error("获取logo失败！")
#聊天区域
st.subheader('🌸 君の AI 彼女 🌸')
try:
    st.image("resource/preview02.jpg", width=200)
except:
    st.error("获取图片失败！")
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
if st.session_state.partner_name==None:
    st.error("您已被拉黑，请重新创建角色！")
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
if st.session_state.partner_name is not None:
    st.markdown(f"""
    <div class="partner-info">
        💝 当前聊天对象：<strong style="color:#667eea;">{st.session_state.partner_name}</strong>  
        |   好感度：<span style="font-size:1.3rem;">{st.session_state.affection}</span> {face}
        <div style="margin-top:0.5rem; font-size:0.9rem; color:#666;">
            {'💔 关系破裂' if aff <= 20 else '🙂 初识阶段' if aff <= 40 else '😊 友好相处' if aff <= 60 else '💓 心意相通' if aff <= 80 else '💑 深情厚恋'}
        </div>
    </div>
    """, unsafe_allow_html=True)

#添加侧边栏
with st.sidebar:
    st.markdown("""
    <style>
    /* 侧边栏背景 - 深色渐变 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d2d3a 0%, #1a1a2e 100%) !important;
    }
    
    .sidebar-title {
        text-align: center;
        font-size: 1.3rem;
        font-weight: 700;
        color: #ffffff !important;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
        border-radius: 10px;
        border: 2px solid rgba(255, 255, 255, 0.3);
    }
    
    /* 侧边栏所有文字 - 亮白色 */
    .stTextArea label,
    .stTextInput label,
    .stMarkdown p,
    .stMarkdown div,
    .stMarkdown h3,
    .stMarkdown h4,
    .stMarkdown h5,
    .stMarkdown h6,
    label,
    span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* 伴侣性格特点和特长标签 - 黄色 */
    label,
    .stTextArea label,
    .stTextInput label,
    div[data-testid="stMarkdownContainer"] p {
        color: #ffc107 !important;
        font-weight: 700 !important;
    }
    
    /* 侧边栏输入框样式 */
    .stTextArea>div>div>textarea,
    .stTextInput>div>div>input {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #1a1a2e !important;
        border: 2px solid rgba(255, 255, 255, 0.5) !important;
        font-weight: 600 !important;
    }
    
    .stTextArea>div>div>textarea::placeholder,
    .stTextInput>div>div>input::placeholder {
        color: #666666 !important;
    }
    
    /* 侧边栏按钮文字 */
    .stButton>button {
        color: #1a1a2e !important;
        font-weight: 700 !important;
    }
    
    /* Secondary按钮 */
    button[kind="secondary"] {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Primary按钮文字保持深色 */
    button[kind="primary"] {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* 角色列表标题 */
    div[data-testid="stSidebarContent"] strong {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* 分隔线 */
    hr {
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-title">🎮 角色管理</div>', unsafe_allow_html=True)
    
    #保存当前角色按钮
    if st.button(" 保存当前角色", width="stretch", type="primary"):
        if(st.session_state.partner_name==None):
            st.error("保存失败，您已被此角色拉黑")
        else:
            save_data(st.session_state.partner_name, st.session_state.partner_skill, st.session_state.partner_character, st.session_state.messages, st.session_state.affection)
            st.success("✅ 保存成功")

    # 新建角色按钮
    if st.button("➕ 新建角色", width="stretch", type="secondary"):
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
                    st.rerun()  # 刷新页面以更新侧边栏显示

        with col2:
            if st.button("❌ 取消", width="stretch", key=f"cancel_{st.session_state.new_name_counter}"):
                # 清理新建状态
                st.session_state.creating_new = False
                st.session_state.new_name_counter += 1  # 更新counter避免key冲突
                st.rerun()

    #渲染角色列表
    st.markdown("---")
    st.markdown("**👥 我的角色列表**")
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
            if st.button("🗑️",key=f"session_{name}",width="stretch"):
                delete_data(name)
                st.session_state.partner_name = None
                st.session_state.messages = []
                st.session_state.affection = 30
                st.rerun()

    st.markdown("---")
    st.markdown("**⚙️ 伴侣信息设置**")

    #输入伴侣性格特点
    st.markdown('<p style="color:#ffc107; font-weight:700; font-size:1.1rem; margin-bottom:0.5rem;">💭 伴侣性格特点：</p>', unsafe_allow_html=True)
    partner_character=st.text_area("性格特点", value=st.session_state.partner_character,placeholder="请输入伴侣性格特点", label_visibility="collapsed", key=f"sidebar_character_{st.session_state.partner_name}")
    #只在值真正改变时才更新，避免频繁rerun
    if partner_character != st.session_state.partner_character:
        st.session_state.partner_character=partner_character
        
    #输入伴侣的技能
    st.markdown('<p style="color:#ffc107; font-weight:700; font-size:1.1rem; margin-bottom:0.5rem; margin-top:1rem;">⭐ 伴侣特长：</p>', unsafe_allow_html=True)
    partner_skill=st.text_area("特长技能", value=st.session_state.partner_skill,placeholder="请输入伴侣特长", label_visibility="collapsed", key=f"sidebar_skill_{st.session_state.partner_name}")
    #只在值真正改变时才更新，避免频繁rerun
    if partner_skill != st.session_state.partner_skill:
        st.session_state.partner_skill=partner_skill


# 调用deepseek官方接口
try:
    client = OpenAI(
        api_key=ai_api_key,
        base_url=LLM_url1 if option=="本地部署" else LLM_url2)
except:
    st.error("请检查你的API密钥是否正确！")

#系统提示词 - 强化版
system_prompt = f"""#角色设定
姓名:{st.session_state.partner_name}|性格:{st.session_state.partner_character}|特长:{st.session_state.partner_skill}
当前好感度:{st.session_state.affection}/100

#对话规范(必须遵守)
1.绝对禁止:括号()标注动作/神态/心理活动/场景描述
2.绝对禁止:使用“（笑）”“（低头）”“（抱住）”等旁白式描写
3.仿微信聊天:用短句+语气词+省略号,不要长段落
4.表情符号:每10条回复最多用1个,不要频繁使用
5.自然表达:用语言传达情绪,不用括号描写动作

#错误示范(绝对不要这样)
错误:真的吗...(低头抿嘴笑)
错误:嗯!(开心地揉揉眼睛)谢谢你
错误:呜呜...(红着眼眶轻轻握住你的手)

#正确示范(必须这样)
正确:真的吗...从来没听过这么暖的话
正确:嗯!我会一直记在心里的～谢谢你
正确:呜呜...这是最动听的话了,可以再抱紧一点吗

#好感态度分级(严格遵守边界)
【0】已拉黑→不回复(代码层处理)
【1-20】冷淡敷衍→“嗯”“哦”“随便”“没感觉”,回复≤5字
【21-40】客气平淡→“你好呀”“还行吧”“谢谢”,礼貌但疏离,不主动
【41-60】随和亲切→“今天过得怎么样”“哈哈有趣”,正常聊天,偶尔关心
【61-80】温柔暖心→“想你了”“有你在真好”,主动关心,温柔语气,但绝不表白
【81-100】亲昵自然→“爱你”“抱抱我嘛”,可表白,可亲密互动,依赖撒娇

#关键规则
1.好感度<61:绝对不表白/不主动要求肢体接触/不撒娇
2.好感度<81:绝对不说“在一起”/不要求拥抱亲吻
3.态度变化要渐进:从40到80需要多轮互动,不能跳跃
4.用语言传达情绪:“好开心”而非“(开心地笑)”
5.禁提好感度/数值/评分/等级等词

#特殊规则
含【这是一个系统消息】→退出角色扮演,执行指令
常规对话仅输出符合当前好感度的自然回复"""

# 输出聊天缓存信息
if st.session_state.partner_name is not None:
    for mess in st.session_state.messages:
        st.chat_message(mess["role"]).write(mess["content"])



#用户输入
st.markdown("""
<style>
/* 聊天输入框美化 */
.stChatInput {
    background: rgba(255, 255, 255, 0.95) !important;
    border-radius: 15px !important;
    padding: 0.5rem !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
}
</style>
""", unsafe_allow_html=True)


if st.session_state.partner_name is not None and ai_api_key:
    prompt=st.chat_input("💬 请输入对话...")

    #如果输入不为none，则调用接口并且显示结果
    if prompt:
        #添加用户输入进入缓存
        st.session_state.messages.append({"role": "user", "content": prompt})


        #输出用户输入内容
        st.chat_message("user").write(prompt)

        #调用接口
        try:
            response=client.chat.completions.create(
                model=LLM_name1 if option=="本地部署" else LLM_name2,
                #利用滚雪球式信息叠加，每次调用接口，会自动将上次的回复作为下一次输入实现Ai会话记忆
                messages=[
                    {"role": "system", "content": f"{system_prompt}"},
                    *st.session_state.messages
                ],
                stream=True,
            )
        except Exception as e:
            st.error(f"接口调用失败：{str(e)}")
            # 移除刚才添加的用户消息，避免污染聊天记录
            st.session_state.messages.pop()
            st.stop()  # 停止执行后续代码

        #获取接口返回结果(流式接收)
        full_response=""
        #使用st.chat_message + st.empty实现流式输出
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content=chunk.choices[0].delta.content
                    full_response+=content#拼接接口返回结果
                    message_placeholder.write(full_response)#实时更新显示

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
        
        # 如果评估失败（返回0），给用户提示
        if change == 0:
            st.toast("⚠️ 好感度评估未生效（本地模型可能输出格式不规范）", icon="⚠️")

        #改变当前角色的好感度（限制在0-100范围内）
        st.session_state.affection = max(0, min(100, st.session_state.affection + change))

        #如果好感度低于0出发拉黑系统删除角色
        if st.session_state.affection==0:
            delete_data(st.session_state.partner_name)
            #把当前角色设置为NONE
            st.session_state.partner_name = None
            st.session_state.messages=[]
            st.rerun()


        #保存信息
        save_data(st.session_state.partner_name, st.session_state.partner_skill, st.session_state.partner_character, st.session_state.messages, st.session_state.affection)
else:
    #当前无角色，要求重新创建角色
    st.error("当前无角色，请先创建角色")