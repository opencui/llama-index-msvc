## Retrieval augmented generation on markdown

Markdown is a lightweight markup language that allows you to format text in a way that is easy to  read and
write. It's commonly used for creating content that will be displayed on the web, such as in websites,
blogs, forums, and documentation. Markdown is designed to be simple and intuitive, allowing you to use
plain text to add formatting elements like headers, lists, links, images, and more, without the need for
complex HTML or other formatting languages.

Because of the simplicity of its markup language, it is fairly easy to parse the semantic structure
from the markdown file, for example, headers are generally used as title for subsections. These structure
can then be used during both the index and retrieval phase for better performance. MdRag is a simple
retrieval augmented generation system focus on markdown files.

MdRag also allow you to use different prompt using OpenAI chat like API to build different chat experience,
while bring your private text to LLMs (use llamaindex), simply use the handlebars via pybars3. Note
it is possible to use other LLMs (llama v2 for example) for generation using GenossGPT.


```python

# This is the main function that mdrag provides. Notice the prompt is for system, and it uses the handlebars
# templating, with {{query}} representing the current user input, and {{context}} for retrieved text.
# each turn is a dictionary with two keys: role and content.

prompt = "We have provided context information below. \n" 
    "---------------------\n"
    "{{context}}"
    "\n---------------------\n"
    "Given this information, please answer the question: {{query}}\n"

def query(turns: list[dict[str, str]], prompt: str = prompt): str
```

### Install

- pip install -r requirements.txt

### Test Command

- OPENAI_API_KEY="" pytest test.py

### Run Command

- OPENAI_API_KEY="" python main.py
