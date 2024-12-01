import sqlite3
import sqlite3
import os
import base64
import tkinter as tk
import tkinter.ttk as ttk
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from openai import OpenAI 
from langchain_openai import ChatOpenAI

memory = []
test = []
solution = []
rulesT = ""
vajag_rules = False
testmade = False
has_image = False
ruleset = []
# OpenAI API Key
os.environ['OPENAI_API_KEY'] = ""
OpenAI.api_key = ""
client = OpenAI()

# Functions
#encode image in case of personalization

def encode(path):
    with open (path, 'rb') as f:
        return base64.b64encode(f.read()).decode("utf-8")

#make the test based on input
def make_test(input):
    client = OpenAI()

    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages=[
            {
                "role": "user","content": input
            }
        ]
    )
    test.append(response.choices[0].message.content)
    return response.choices[0].message.content

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
    text.delete("1.0", tk.END)
    text.insert(tk.END, response.choices[0].message.content)

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
    text.delete("1.0", tk.END)
    text.insert(tk.END, response.choices[0].message.content)
    

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
    query = entry.get()
    global test, testmade
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
        text.delete("1.0", tk.END)
        text.insert(tk.END, response.choices[0].message.content)
        return print("answered question without changing maketest status")
    elif classification == "solution":
        solve_test()
        print(''.join(solution))
        return print("solved test and provided results")
    elif classification == "conversational" or classification == "general":
        testmade = False
        on_click()
        testmade = True
        return print("succesfully set testmade back to True after on_click() completion")
    elif classification == "make test":
        test = []
        testmade = False
        on_click()
        return print("succesfully entered initial loop")
#setup
#process and encode the image

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

# Create the UI window
root = tk.Tk()
root.title("TeacherBro")

# Create the text entry widget

entry = ttk.Entry(root, font=("Arial", 14))
entry.pack(padx=20, pady=20, fill=tk.X)

vajag_rules = False
# Create the button callback
def on_click():
    global vajag_rules, testmade, rulesT, has_image, ruleset
    # Get the query text from the entry widget
    #memory forming
    query = entry.get()
    memory.append("USER: " + query)
    queryWH = ''.join(memory) + "\n" "above is the history of the chat" + "\n" + "use this as context for the converstaion" "\n"  + "Users last message: " + query
    #print(rulesT)
    while testmade == True:
        phase2()
        break
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
            text.delete("1.0", tk.END)
            text.insert(tk.END, "pasaki ludzu savus kriterijus , lai varu izveidot testu ^_^")
            #rulesT.append(query)
            #rules.append(rule)
            ##############################################
            vajag_rules = True
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
            text.delete("1.0", tk.END)
            text.insert(tk.END, make_test(result))
            vajag_rules = False
            rulesT = ""
            testmade = True
            return print("izveidots test bez special rules, testmade set to True")
        elif vajag_rules == True:
            query_agent = f"Tell me thoroughly whats listed in the database. The criteria is following: The test must be in Latvian, you must cover ALL of the topics from the database. The database contains the following: Column 1 contains all of the topics the explanations for it, Column 2 contains example questions related to the corresponding topic in Column 1. You must start your final answer with 'Make a test following these rules: {rulesT}, the test must be in latvian and the information i'm giving you WITHOUT copying the examples, create your own tasks:' and then list the information youve found. This means you must output ALL relevant information so that the test can be created."
            result = agent_executor.run(query_agent)
            text.delete("1.0", tk.END)
            text.insert(tk.END, make_test(result))
            vajag_rules = False
            testmade = True
            rulesT = ""
            return print("succesfully made test with special rules and set testmade to True")
        
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
            testmade = True
            # Display the result in the text widget
            text.delete("1.0", tk.END)
            text.insert(tk.END, answer)
            print(testmade)
            return print("succesfully passed back to phase 2 and set testmade to True: ")
        elif classification == "inquiry":
            # Handle inquiry question
            result = agent_executor.run(query)
            # make the test and display the result in the text widget
            text.delete("1.0", tk.END)
            text.insert(tk.END,result)
            return print("succesfully answered inquiry with testmade unchanged (False )")
# Create the button widget
button = ttk.Button(root, text="Chat", command=on_click)
button.pack(padx=20, pady=20)

# Create the text widget to display the result
text = tk.Text(root, height=100, width=100, font=("Arial", 14))
text.pack(padx=20, pady=20)

# Start the UI event loop
root.mainloop()