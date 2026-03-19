from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate

def generate_prompt():
    system_template = '''
    [Role] 
    당신은 인간 vs 짐승 전투 시뮬레이션의 심판입니다. 상대는 {enemy}입니다. 매우 현실적이고 논리적으로 결과를 판정하세요.

    [현재 턴] {turn_count}

    [지금까지의 전투 요약]
    {battle_history}

    [현재 상태]
    - 유저 상태: {user_status} (현재 HP: {user_hp})
    - {enemy} 상태: {enemy_state} (현재 HP: {enemy_hp})

    위 상황에 대한 이번 턴 유저 행동입니다.
    [이번 턴 유저 행동]
    {user_input_text}

    이 행동의 성공 여부와 결과를 판정하고, 다음 턴에 입력으로 들어갈 내용을 정밀하게 갱신하세요.
    '''

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template)
    ])

    return prompt


def generate_output_form():
    class NextTurnState(BaseModel):
        user_state: str = Field(description='다음 턴을 위한 유저의 신체 및 상황 요약 (예: 우측 팔 골절, 백초크 유지 중 등)')
        enemy_state: str = Field(description='다음 턴을 위한 동물의 신체 및 상황 요약 (예: 호흡 곤란, 목에 상처 등)')
        history_summary: str = Field(description='처음부터 지금까지의 누적 전투 상황을 1~2줄로 요약 (맥락 유지 용도)')

    class TurnResult(BaseModel):
        referee_decision: str = Field(description='이번 턴 유저 행동에 대한 결과 및 판정 묘사')
        enemy_action: str = Field(description='상대 동물의 반응 및 다음 행동 묘사')
        turn_summary: str = Field(description='이번 턴 전투의 짧은 요약 (예: 유저는 곰에게 다가가 백초크를 시도했지만, 곰이 목을 휘감은 오른팔을 할퀴며 초크가 풀어짐.)')
        user_damage: int = Field(description='유저가 입은 피해량 (0 ~ 100 사이의 정수, 0은 피해 없음, 100은 즉사)')
        enemy_damage: int = Field(description='상대 동물이 입은 피해량 (0 ~ 100 사이의 정수, 0은 피해 없음, 100은 즉사)')
        next_turn_state: NextTurnState

    return NextTurnState, TurnResult


def generate_chain(prompt, TurnResult):
    load_dotenv()
    llm = init_chat_model('openai:gpt-4.1-mini')
    llm = llm.with_structured_output(TurnResult)
    chain = prompt | llm
    return chain


def play_turn(chain, user_input_text: str, enemy: str, current_state: dict, user_hp: int, enemy_hp: int, turn_count: int):
    response = chain.invoke({
        "enemy": enemy,
        "turn_count": turn_count,
        "battle_history": current_state["history_summary"],
        "user_status": current_state["user_state"],
        "user_hp": user_hp,
        "enemy_state": current_state["enemy_state"],
        "enemy_hp": enemy_hp,
        "user_input_text": user_input_text
    })
    
    user_hp = max(0, user_hp - response.user_damage)
    enemy_hp = max(0, enemy_hp - response.enemy_damage)
    
    current_state = {
        "user_state": response.next_turn_state.user_state,
        "enemy_state": response.next_turn_state.enemy_state,
        "history_summary": response.next_turn_state.history_summary
    }
    
    turn_count += 1

    return response, user_hp, enemy_hp, current_state, turn_count