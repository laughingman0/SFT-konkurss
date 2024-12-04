from flask import Flask, request, render_template
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
        model = "o1-preview",
        messages=[
            {
                "role": "user","content": input
            }
        ]
    )
    test.append(response.choices[0].message.content)
    structured_output = structuringOutput(response.choices[0].message.content)
    print(structured_output)
    print(response.choices[0].message.content)
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
    model = "o1-preview",
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
        model = "o1-preview",
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
    print(classification)
    return classification

# main function after test has been created
def phase2():
    query = request.form['request']
    global test, testmade, vajag_rules, P2ConvHasBeenCalled
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
        solution = print(''.join(solution))
        return render_template("index1.html", answer=solution)
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
    handle_parsing_errors=True
)
#structuring responses

class Structuring(BaseModel):
    TestName: str
    Context_for_tasks_and_tasks_themselves: list[str]
    conclusions: str
def structuringOutput(input):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Extract the information from the test. Make sure to fully extract the tasks from the test given, including context for the task and what you have to do in it."},
            {"role": "user", "content": input}
        ],
    response_format=Structuring,
)
    message = completion.choices[0].message.parsed
    return {
        "TestName": message.TestName,
        "Context_for_tasks_and_tasks_themselves": message.Context_for_tasks_and_tasks_themselves,
        "conclusions": message.conclusions
    }

@app.route('/', methods=['POST'])
def ask_something():
    query = request.form['request']
    global vajag_rules, testmade, rulesT, has_image, ruleset
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
            rulesT = query
        '''
        if has_image == False:
            text.delete("1.0", tk.END)
            text.insert(tk.END, "fotka ir ?")
            if query == "nav":
                has_image == False
            if query == "image.jpg":
                has_image = True
                # placeholder prieks path SITO SATAISIT KKAD
                process_image(query)
                ruleset = ''.join(ruleset)
        '''

        classification = classify_question(query)
        if classification == "test" and rulesT == "":
            
            #seit janotiek rules iegusana
            answer = "pasaki ludzu savus kriterijus , lai varu izveidot testu ^_^"
            vajag_rules = True
            return render_template('index1.html', answer=answer)
            #rulesT.append(query)
            #rules.append(rule)
            ##############################################
            '''
        elif classification == "test" and ruleset:
            query_agent = f"Tell me thoroughly whats listed in the database. The criteria is following: The test must be in Latvian, you must cover ALL of the topics from the database. The database contains the following: Column 1 contains all of the topics the explanations for it, Column 2 contains example questions related to the corresponding topic in Column 1. You must start your final answer with 'Make a test using the information i'm giving you here: {ruleset} and this information WITHOUT using the examples and creating your own tasks:' and then list the information youve found. This means you must output ALL relevant information so that the test can be created."
            result = agent_executor.run(query_agent)
            text.delete("1.0", tk.END)
            text.insert(tk.END, make_test(result))
            vajag_rules = False
            ruleset = []
            testmade = True
            return print("izveidots test bez special rules, testmade set to True")
            '''
        elif rulesT == "nav":
            # Extract information from the database
            query_agent = "Tell me thoroughly whats listed in the database. The criteria is following: The test must be in Latvian, you must cover ALL of the topics from the database. The database contains the following: Column 1 contains all of the topics the explanations for it, Column 2 contains example questions related to the corresponding topic in Column 1. You must start your final answer with 'Make a test using the information i'm giving you WITHOUT using the examples and creating your own tasks:' and then list the information youve found. This means you must output ALL relevant information so that the test can be created."
            result = agent_executor.run(query_agent)
            vajag_rules = False
            structured_output = make_test(result)
            rulesT = ""
            testmade = True
            return render_template('index1.html', **structured_output)
        elif vajag_rules == True:
            query_agent = f"Tell me thoroughly whats listed in the database. The criteria is following: The test must be in Latvian, you must cover ALL of the topics from the database. The database contains the following: Column 1 contains all of the topics the explanations for it, Column 2 contains example questions related to the corresponding topic in Column 1. You must start your final answer with 'Make a test following these rules: {rulesT}, the test must be in latvian and the information i'm giving you WITHOUT copying the examples, create your own tasks:' and then list the information youve found. This means you must output ALL relevant information so that the test can be created."
            result = agent_executor.run(query_agent)
            structured_output = make_test(result)
            vajag_rules = False
            testmade = True
            rulesT = ""
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
            print(testmade)
            if P2ConvHasBeenCalled:
                testmade = True
            return render_template('index1.html', answer=answer)
        elif classification == "inquiry":
            # Handle inquiry question
            result = agent_executor.run(query)
            # make the test and display the result in the text widget
            return render_template("index1.html", answer=result)

if __name__ == '__main__':
    app.run(port=5000)

'''
from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index1.html')

@app.route('/', methods=['POST'])
def ask_something():
    text = request.form['request']

    #text goes to chatGPT
    #chatGPT gives answer

    answer = "Lorem ipsum odor amet, consectetuer adipiscing elit. Eu mus eros tempor nostra sapien habitasse. Duis porttitor inceptos orci tortor; fames eros. Interdum nostra potenti curae curae, neque ante fames sapien amet. Magnis laoreet urna dui aptent, dolor erat fermentum nam. Suscipit egestas maximus platea ullamcorper ante parturient commodo luctus aenean. Magna a cursus sociosqu est est quam. Mus sociosqu quisque sit viverra nascetur nulla tristique. Ultrices lacus gravida lobortis morbi tempor auctor consectetur velit. Litora mattis id ridiculus cubilia purus ultrices turpis mus."

    return render_template('index1.html', answer=answer)

if __name__ == '__main__':
    app.run(port=5000)

'''