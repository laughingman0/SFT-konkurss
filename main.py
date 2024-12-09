from flask import Flask, request, render_template, redirect
import sqlite3
import sqlite3
import os
import base64
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from openai import OpenAI 
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

#initial variables
app = Flask(__name__)
memory = []
test = []
solution = []
rulesT = ""
vajag_rules = False
testmade = False
has_image = False
ruleset = []
P2ConvHasBeenCalled = False
arerules = False
# OpenAI API Key
os.environ['OPENAI_API_KEY'] = ""
OpenAI.api_key = ""
client = OpenAI()

#functions backend

#function to encode image in case of personal test
def encode(path):
    with open (path, 'rb') as f:
        return base64.b64encode(f.read()).decode("utf-8")
    
@app.route('/')
def home():
    return render_template('index1.html')

#make the test based on input
def make_test(input):
    global client

    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages=[
            {
                "role": "user","content": input
            }
        ]
    )
    test.append(response.choices[0].message.content)
    structured_output = structuringOutput(response.choices[0].message.content)
    return structured_output

#process the image for use by o1
def process_image(path):
    b64_img = encode(path)
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "List only the mathematical equations you see."},
        {   
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{b64_img}",
            },
            },
        ],
        }
    ],
    )
    process_response = response.choices[0].message.content
    ruleset.append(process_response)

# solve and grade the work done by the student
def solve_and_correct_image():
    query = "the following is a test by a student. check it and grade it percentually. " + "\n" + ''.join(process_image())
    response = client.chat.completions.create(
    model = "gpt-4o-mini",
    messages=[
        {
            "role": "user","content": query,
        }
        ]
    )
    solution.append(response.choices[0].message.content)
    answer = response.choices[0].message.content
    return render_template('index1.html', answer=answer)
    
def solve_test():
    query = "the following is a test. solve it and provide answers to all questions. " + "\n" + ''.join(test)
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages=[
            {
                "role": "user","content": query,
                }
                ]
    )
    solution.append(response.choices[0].message.content)
    answer = response.choices[0].message.content
    return render_template('index1.html', answer=answer)

#classify the users input (i.e. what he wants)
def classify_question(user_question):
    prompt = f"Classify the following question as whether it wants you to make a test or if it is a conversational question or if it is a question which inquires about the test or whether it wants a solution to the test., answer in 1 word - either general, or test or inquiry or solution: '{user_question}'"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an assistant that helps classify questions."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract classification from the response
    classification = response.choices[0].message.content.strip().lower()
    return classification

# main function after test has been created
def phase2():
    query = request.form['request']
    global test, testmade, vajag_rules, P2ConvHasBeenCalled, solution
    test_fixed = ''.join(test)
    classification = classify_question(query)
    if classification == "inquiry":
        response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a helpful assistant that answers questions about the following test: {test_fixed}."},
                    {"role": "user", "content": query }
                ]
            )
        answer = response.choices[0].message.content
        return render_template('index1.html', answer=answer)
        #return print("answered question without changing maketest status")
    elif classification == "solution":
        solve_test()
        solution =''.join(solution)
        structured_output = structuringOutput(solution)
        return render_template("index1.html", **structured_output)
        #return print("solved test and provided results")
    elif classification == "conversational" or classification == "general":
        P2ConvHasBeenCalled = True
        testmade = False
        return ask_something()
        #return print("succesfully set testmade back to True after on_click() completion")
    elif classification == "test":
        test = []
        testmade = False
        vajag_rules = False
        P2ConvHasBeenCalled = False
        return ask_something()
        #return print("succesfully entered initial loop")

#setup 
# Connect to the database and execute the SQL script
conn = sqlite3.connect('mathdb2.db')
with open('mathdb_new_new.sql', 'r',encoding='cp1252', errors='replace',) as f:
    sql_script = f.read()
conn.executescript(sql_script)
conn.close()

llm = ChatOpenAI(model = "gpt-4o-mini")
# Create the agent executor
db = SQLDatabase.from_uri("sqlite:///./mathdb2.db")
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(
    llm = ChatOpenAI(model = "gpt-4o-mini"),
    toolkit=toolkit,
    verbose=True,
    handle_parsing_errors="Check your output and make sure it conforms, use the Action/Action Input syntax",
)
#structuring responses
def criteria(input):
    global arerules
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "you are a Helper that helps figure out whether the user has rules mentioned or not. If he does, return True. If he doesn't, return False. For example: if a user's input would be 'no', or 'no criteria', you would return False, if the user's input would be '2 exercises, make it easy', then you would return True." },
            {"role": "user", "content": input }
        ]
    )
    answer = completion.choices[0].message.content.strip()
    if answer == "True" or answer == True:
        arerules = True
        return arerules
    elif answer == "False" or answer == False:
        arerules = False
        return arerules

class Structuring(BaseModel):
    TestName: str
    Context_for_tasks_and_tasks_themselves: list[str]
    conclusions: str
    
def structuringOutput(input):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Your only job is do structure the text given to you by the user following the response format. Do not add any of your own text, and do not remove any of the text from the original text, all you have to do is structure it. Structure a single task and its context and its questions under one object and do this for all tasks."},
            {"role": "user", "content": input}
        ],
    response_format=Structuring,
)
    message = completion.choices[0].message.parsed
    return {
        "TestName" : message.TestName,
        "Context_for_tasks_and_tasks_themselves": message.Context_for_tasks_and_tasks_themselves,
        "conclusions": message.conclusions
        
    }

@app.errorhandler(500)
def internal_server_error(error):
    global arerules, testmade, rulesT, vajag_rules
    app.logger.error(f" ILJIC SERVEERS CRASOJA SALABO, server error:{error}")
    vajag_rules = False
    rulesT = ""
    testmade = True
    arerules = False
    return redirect(request.url),500

@app.route('/', methods=['POST'])
def ask_something():
    query = request.form['request']
    global vajag_rules, testmade, rulesT, has_image, ruleset, arerules
    #text goes to chatGPT
    #chatGPT gives answer
    # Get the query text from the entry widget
    #memory forming
    memory.append("USER: " + query)
    queryWH = ''.join(memory) + "\n" "above is the history of the chat" + "\n" + "use this as context for the converstaion" "\n"  + "Users last message: " + query
    #print(rulesT)
    while testmade == True:
        return phase2()
    if testmade == False:
        if vajag_rules == True:
            arerules = criteria(query)
        if arerules == True:
            rulesT = query
            pass
        else:
            pass

        classification = classify_question(query)
        if classification == "test" and rulesT == "":
            
            #seit janotiek rules iegusana
            answer = "Is there any criteria you would like me to follow? ^_^"
            vajag_rules = True
            return render_template('index1.html', answer=answer)
            #rulesT.append(query)
            #rules.append(rule)
            ##############################################

        elif arerules == False and vajag_rules == True:
            # Extract information from the database
            query_agent = "Tell me thoroughly whats listed in the database. The criteria is following: you must cover ALL of the topics from the database. The database contains the following: Column 1 contains all of the topics the explanations for it, Column 2 contains example questions related to the corresponding topic in Column 1. You must start your final answer with 'Make a test using the information i'm giving you WITHOUT using the examples and creating your own tasks:' and then list the information youve found. This means you must output ALL relevant information so that the test can be created."
            result = agent_executor.run(query_agent)
            vajag_rules = False
            structured_output = make_test(result)
            rulesT = ""
            testmade = True
            return render_template('index1.html', **structured_output)
        elif arerules == True and vajag_rules == True:
            query_agent = f"Tell me thoroughly whats listed in the database. The criteria is following: you must cover ALL of the topics from the database. The database contains the following: Column 1 contains all of the topics the explanations for it, Column 2 contains example questions related to the corresponding topic in Column 1. You must start your final answer with 'Make a test following these rules given by the user: '{rulesT}', and the information i'm giving you WITHOUT copying the examples, create your own tasks:' and then list the information youve found. This means you must output ALL relevant information so that the test can be created."
            result = agent_executor.run(query_agent)
            structured_output = make_test(result)
            vajag_rules = False
            testmade = True
            rulesT = ""
            arerules = False
            return render_template('index1.html', **structured_output)
        
        elif classification == "conversational" or classification == "general" and vajag_rules == False:
            # Handle general conversational question

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. "},
                    {"role": "user", "content": queryWH }
                ]
            )
            # Extract answer from GPT response
            answer = response.choices[0].message.content.strip()
            memory.append("SYSTEM: "+ answer)
            # Display the result in the text widget
            if P2ConvHasBeenCalled:
                testmade = True
            return render_template('index1.html', answer=answer)
        elif classification == "inquiry":
            # Handle inquiry question
            result = agent_executor.run(query)
            # make the test and display the result in the text widget
            return render_template("index1.html", answer=result)
        else:
            return render_template('index1.html', answer="Sorry, I didn't understand your question.")

if __name__ == '__main__':
    app.run(port=5000)

