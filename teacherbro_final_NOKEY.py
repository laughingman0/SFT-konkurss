import sqlite3
import sqlite3
import os

import tkinter as tk
import tkinter.ttk as ttk
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from openai import OpenAI 
from langchain_openai import ChatOpenAI


# OpenAI API Key
os.environ['OPENAI_API_KEY'] = ""
OpenAI.api_key = ""
client = OpenAI()

# Function to determine if the question is database-related
def classify_question(user_question):
    # Send the question to GPT to classify
    prompt = f"Classify the following question as whether it wants you to make a test, or if it is a conversational question, answer in 1 word - either general, or test: '{user_question}'"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
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

# Connect to the database and execute the SQL script
conn = sqlite3.connect('test2.db')
with open('mathdb.sql', 'r',encoding='cp1252', errors='replace',) as f:
    sql_script = f.read()
conn.executescript(sql_script)
conn.close()

llm = ChatOpenAI(model = "gpt-4o-mini")
# Create the agent executor
db = SQLDatabase.from_uri("sqlite:///./test2.db")
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

# Create the button callback
def on_click():
    # Get the query text from the entry widget
    query = entry.get()

    # Run the query using the agent executor
    classification = classify_question(query)
    if classification == "test":
        # Extract
        # make the test from the database
        make_test_q = "you must create a unique test with 10 tasks with your own numbers and tasks based on the information in the database. The criteria is following: The test must be in Latvian, The test must cover ALL of the topics from the database, the tasks must NOT equal the example tasks in the database, the tasks MUST only be about the topics covered in the database. The database contains the following: Column 1 contains all of the topics the explanations for it, Column 2 contains example questions related to the corresponding topic in Column 1."
        result = agent_executor.run(make_test_q)

        # Display the result in the text widget
        text.delete("1.0", tk.END)
        text.insert(tk.END, result)
    elif classification == "conversational" or classification == "general":
        # Handle general conversational question
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. speak only in latvian."},
                {"role": "user", "content": query}
            ]
        )
        # Extract answer from GPT response
        answer = response.choices[0].message.content.strip()
        # Display the result in the text widget
        text.delete("1.0", tk.END)
        text.insert(tk.END, answer)

# Create the button widget
button = ttk.Button(root, text="Chat", command=on_click)
button.pack(padx=20, pady=20)

# Create the text widget to display the result
text = tk.Text(root, height=20, width=100, font=("Arial", 14))
text.pack(padx=20, pady=20)

# Start the UI event loop
root.mainloop()




