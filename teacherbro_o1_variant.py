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
        model = "o1-preview",
        messages=[
            {
                "role": "user","content": input
            }
        ]
    )
    test.append(response.choices[0].message.content)
    return response.choices[0].message.content
#process the image for use by o1
def process_image():
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
    return process_response

# solve and grade the work done by the student
def solve_and_correct():
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

#classify the users input (i.e. what he wants)
def classify_question(user_question):
    prompt = f"Classify the following question as whether it wants you to make a test or if it is a conversational question or if it is a question which inquires about the test., answer in 1 word - either general, or test or inquiry: '{user_question}'"

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

#setup
#process and encode the image
path = "image.jpg"
b64_img = encode(path)

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

#autisma atbalsta funkcija
def autism():
    text.delete("1.0", tk.END)
    text.insert(tk.END, "nosauc visus noteikumus kuce")
    while not rulesT:
        rulesT = entry.get()
    if rulesT == "nav":
        return rulesT






# Create the button callback
def on_click():
    # Get the query text from the entry widget
    query = entry.get()
    memory.append("USER: " + query)
    queryWH = ''.join(memory) + "\n" "above is the history of the chat" + "\n" + "use this as context for the converstaion" "\n"  + "Users last message: " + query 
    
    classification = classify_question(query)
    if classification == "test":
        '''
        #seit janotiek rules iegusana
        text.delete("1.0", tk.END)
        text.insert(tk.END, "nosauc visus noteikumus kuce")
        rulesT.append(query)
        #rules.append(rule)
        ##############################################
        '''
        autism()
        if rulesT == "nav":
            # Extract information from the database
            query_agent = "Tell me thoroughly whats listed in the database. The criteria is following: The test must be in Latvian, you must cover ALL of the topics from the database. The database contains the following: Column 1 contains all of the topics the explanations for it, Column 2 contains example questions related to the corresponding topic in Column 1. You must start your final answer with 'Make a test using the information i'm giving you WITHOUT using the examples and creating your own tasks:' and then list the information youve found. This means you must output ALL relevant information so that the test can be created."
            result = agent_executor.run(query_agent)
            text.delete("1.0", tk.END)
            text.insert(tk.END, make_test(result))
        else:
            #rules = ''.join(rules)
            query_agent = "Tell me thoroughly whats listed in the database. The criteria is following: The test must be in Latvian, you must cover ALL of the topics from the database. The database contains the following: Column 1 contains all of the topics the explanations for it, Column 2 contains example questions related to the corresponding topic in Column 1. You must start your final answer with 'Make a test using these rules: '{rulesT}' and this information i'm giving you WITHOUT using the examples and creating your own tasks:' and then list the information youve found. This means you must output ALL relevant information so that the test can be created."
            result = agent_executor.run(query_agent)
            text.delete("1.0", tk.END)
            text.insert(tk.END, make_test(result))

    elif classification == "conversational" or classification == "general":
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
        text.delete("1.0", tk.END)
        text.insert(tk.END, answer)
    elif classification == "inquiry":
        # Handle inquiry question
        result = agent_executor.run(query)
        # make the test and display the result in the text widget
        text.delete("1.0", tk.END)
        text.insert(tk.END,result)

# Create the button widget
button = ttk.Button(root, text="Chat", command=on_click)
button.pack(padx=20, pady=20)

# Create the text widget to display the result
text = tk.Text(root, height=100, width=100, font=("Arial", 14))
text.pack(padx=20, pady=20)

# Start the UI event loop
root.mainloop()