import os
from dotenv import load_dotenv, find_dotenv
from typing import List, Dict

import chainlit as cl
from vn import vn
from llama_index.core.base.llms.types import ChatMessage
from llama_index.llms.azure_openai import AzureOpenAI

_ = load_dotenv(find_dotenv())

api_key=os.environ["AZURE_OPENAI_API_KEY"]
azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
api_version = os.environ["AZURE_API_VERSION"]

def prepare_chat_history(history: List[Dict[str, str]]) -> List[ChatMessage]:
    return [ChatMessage(**chat_history_dict) for chat_history_dict in history]

@cl.on_chat_start
async def on_chat_start():
    history = []
    llm = AzureOpenAI(
        model="gpt-4o",
        deployment_name=os.environ["AZURE_OPENAI_GPT4O_DEPLOYMENT_NAME"],
        api_key = api_key,
        azure_endpoint = azure_endpoint,
        api_version = api_version,
        timeout = 120.0,
        temperature = 0,
    )
    cl.user_session.set("llm", llm)
    cl.user_session.set("history", history)

@cl.on_message
async def on_message(message: cl.Message):
    await chain(human_query = message.content)

@cl.step(type="tool", language="sql", name="write_sql")
async def gen_query(human_query: str):
    sql = vn.generate_sql(human_query)
    return sql

@cl.step(type="tool", name="execute_sql")
async def execute_query(query):
    current_step = cl.context.current_step
    df = vn.run_sql(query)
    current_step.output = df.to_markdown(index=False)
    return df

@cl.step(type="tool", name="plot", language="python")
async def plot(human_query, sql, df):
    current_step = cl.context.current_step
    plotly_code = vn.generate_plotly_code(
        question=human_query,
        sql=sql,
        df=df
    )
    current_step.output = plotly_code
    fig = vn.get_plotly_figure(plotly_code=plotly_code, df=df, dark_mode=True)
    return fig

@cl.step(type="llm", name="follow_up")
async def generate_follow_up(human_query, sql, df):
    current_step = cl.context.current_step
    questions = vn.generate_followup_questions(
        question=human_query,
        sql=sql,
        df=df,
    )
    questions = questions[:3] #we're only taking 3 follow-ups
    current_step.output = ", ".join(questions)
    return questions

@cl.step(type="run", name="run_text_to_sql_engine")
async def chain(human_query: str):
    ## Generate SQL query
    sql_query = await gen_query(human_query)
    
    ## Get dataframe from executing SQL query
    df = await execute_query(sql_query)
    
    ## Get plotly object from plot
    fig = await plot(
        human_query = human_query,
        sql = sql_query,
        df = df
    )
    
    ## Generate follow-up questions
    follow_ups = await generate_follow_up(
        human_query = human_query,
        sql = sql_query,
        df = df
    )
    
    actions = [
        cl.Action(
            name="question",
            payload = {"value": question},
            label = question
        ) for question in follow_ups
    ]
    
    elements = [
        cl.Plotly(name="chart", figure=fig, display="inline"),
        cl.Dataframe(data=df, display="inline", name="Dataframe")
    ]
    
    ## Generate insights    
    history = cl.user_session.get("history")
    history.append(
        {
            "role": "user",
            "content": human_query + f"Data:\n\n{df}",
        }
    )
    chat_history = prepare_chat_history(history)
    llm = cl.user_session.get("llm")
    
    msg = cl.Message("", type="assistant_message")
    response = llm.stream_chat(chat_history)
    final_response = ""
    
    ### Stream response
    for chunk in response:
        await msg.stream_token(chunk.delta)
        final_response += chunk.delta
    
    ## Update session chat history
    history.append(
        {
            "role": "assistant",
            "content": final_response
        }
    )
    cl.user_session.set("history", history)
    
    msg.elements = elements
    msg.actions = actions
    await msg.send()
    
@cl.action_callback(name="question")
async def action_callback(action):
    message = action.payload['value']
    await chain(message)

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="What is the highest stock price for Illumina?",
            message="What is the highest ever stock price for Illumina?",
            icon="public/max_price.png",
        ),
        cl.Starter(
            label="NVIDIA overview",
            message="Give me an overview of NVIDIA's share price from 2020-2024",
            icon="public/chart.png",
        ),
        cl.Starter(
            label="Longest bull run",
            message="What is the longest running uptrend for Apple share prices?",
            icon="public/bullrun.png",
        )
    ]