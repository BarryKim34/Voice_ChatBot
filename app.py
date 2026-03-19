import streamlit as st
import base64, io
from dotenv import load_dotenv
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text
from src.game import select_enemy
from src.model import generate_prompt, generate_output_form, generate_chain, play_turn

# --- 환경 설정 ---
load_dotenv()
st.set_page_config(page_title="그 정도는 내가 이기지~", page_icon="🥊", layout="centered")

# --- TTS 자동 재생 함수 ---
def play_tts_autoplay(text):
    if not text:
        return
    try:
        tts = gTTS(text=text, lang='ko')
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        b64 = base64.b64encode(audio_fp.getvalue()).decode()
        md = f"""
            <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"TTS 재생 중 오류 발생: {e}")

# --- 세션 상태 초기화 ---
if 'game_started' not in st.session_state:
    st.session_state.update({
        'game_started': False,
        'chat_history': [],
        'user_hp': 100,
        'enemy_hp': 100,
        'turn_count': 1,
        'current_state': None,
        'enemy': None,
        'enemy_feature': None,
        'last_response': None
    })

# --- 사이드바: 생존 리포트 ---
with st.sidebar:
    st.header("🩸 실시간 생존 리포트")
    st.divider()
    try:
        with open("logo.png", "rb") as image_file:
            b64_logo = base64.b64encode(image_file.read()).decode()
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 0px;">
                <img src="data:image/png;base64,{b64_logo}" style="width: 100%; max-width: 130px;">
            </div>
            """, unsafe_allow_html=True)
    except FileNotFoundError:
        st.write("🔥 **그 정도는 내가 이기지~**")

    st.divider()
    
    if st.session_state.enemy:
        st.subheader("👤 나 (Player)")
        st.metric("HP", f"{st.session_state.user_hp}%")
        st.progress(max(0, st.session_state.user_hp) / 100)
        
        st.divider()
        
        st.subheader(f"👾 {st.session_state.enemy}")
        st.metric("적 HP", f"{st.session_state.enemy_hp}%")
        st.progress(max(0, st.session_state.enemy_hp) / 100)
        
        st.divider()
        if st.button("🏳️ 도망치기 (게임 리셋)"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        st.info("전투를 시작하면 상태가 표시됩니다.")

# --- 메인 화면 ---
st.title("🔥 그 정도는 내가 이기지~")

if not st.session_state.game_started:
    # 1. 시작 화면
    if st.session_state.enemy is None:
        st.session_state.enemy, st.session_state.enemy_feature, st.session_state.current_state = select_enemy()

    st.markdown(f"""
    ### 🛑 "오늘의 대결 상대: {st.session_state.enemy}"
    당신의 자신감이 생물학적 한계를 넘을 수 있을까요?
    
    평소 **"야, 원숭이 정도는 싸우면 내가 이기지!"**라고 허세를 부리셨나요?
    좋습니다. 지금부터 당신의 그 자신감이 생물학적 한계를 넘어서 승리를 쟁취할 수 있을지 증명해 보세요!

    ---
    #### 📜 [전투 규칙]
    1. **턴제 음성 전투**: 하단의 마이크 버튼을 누르고 당신의 행동을 상세하게 말씀해 주세요.
    2. **냉철한 AI 심판**: AI 심판은 **과학적, 해부학적 사실**만을 바탕으로 당신의 행동을 평가합니다.
    3. **HP 시스템**: 당신과 야생 동물의 기본 HP는 100입니다. 먼저 0이 되는 쪽이 패배합니다.
    4. **창의적인 행동**: 주변 환경과 도구를 활용해 생존 확률을 높이세요. 맨몸으로 싸우는 것은 자살 행위입니다.

    ---
    #### 👾 [오늘의 적 정보]
    * **적**: `{st.session_state.enemy}`
    * **상태**: `{st.session_state.enemy_feature}`
    """)
    st.info(f"📍 상대: {st.session_state.enemy} ({st.session_state.enemy_feature})")

    if st.button("🚀 전투 시작 (허세 입증하기)", type="primary", use_container_width=True):
        st.session_state.game_started = True
        st.rerun()

else:
    # 2. 전투 화면
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 하단 제어 섹션 수정 ---
    st.divider()
    
    # 1. 내가 죽었을 때
    if st.session_state.user_hp <= 0:
        st.error("💀 당신은 사망했습니다. 자연의 섭리 앞에 허세는 무용지물이군요.")
        if st.button("🔄 복수하러 가기 (재시작)", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
            
    # 2. 적이 죽었을 때 (HP가 0 이하)
    elif st.session_state.enemy_hp <= 0:
        st.balloons()
        st.success(f"🏆 승리! {st.session_state.enemy}을(를) 물리치고 허세를 증명했습니다!")
        if st.button("🎮 다른 짐승 찾기 (다음 게임)", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
            
    # 3. 그 외 모든 상황 (전투 중) -> 무조건 마이크 표시
    else:
        st.write("#### 👇 마이크를 켜고 다음 행동을 지시하세요!")
        
        user_speech = speech_to_text(
            language='ko',
            start_prompt="🟢 행동 말하기 (클릭)", 
            stop_prompt="🔴 판정 시작 (녹음 중지)",   
            just_once=True,
            key=f'STT_{st.session_state.turn_count}' # 🌟 턴마다 키값을 바꿔서 위젯을 초기화
        )

        if user_speech:
            st.session_state.chat_history.append({"role": "user", "content": user_speech})
            
            with st.spinner("⚖️ 심판 판정 중..."):
                prompt = generate_prompt()
                _, TurnResult = generate_output_form()
                chain = generate_chain(prompt, TurnResult)
                
                response, u_hp, e_hp, next_state, next_turn = play_turn(
                    chain, user_speech, st.session_state.enemy, st.session_state.current_state,
                    st.session_state.user_hp, st.session_state.enemy_hp, st.session_state.turn_count
                )

            st.session_state.user_hp = u_hp
            st.session_state.enemy_hp = e_hp
            st.session_state.current_state = next_state
            st.session_state.turn_count = next_turn
            
            referee_msg = f"🧑‍⚖️ **심판 판정**: {response.referee_decision}\n\n🐾 **상태**: {response.enemy_action}"
            st.session_state.chat_history.append({"role": "assistant", "content": referee_msg})
            
            st.session_state.last_response = f"{response.referee_decision} {response.enemy_action}"
            st.rerun()

    # TTS 재생
    if st.session_state.last_response:
        play_tts_autoplay(st.session_state.last_response)
        st.session_state.last_response = None