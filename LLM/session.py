import ollama
from ollama import ChatResponse
import asyncio


class ChatSession:
    client = ollama.AsyncClient()
    def __init__(self, tools: list[callable]):
        self.tools_list = [self._respond_to_user]+tools
        self.tools_dict = {tool.__name__: tool for tool in self.tools_list}
        self.model = "llama3.2"
        self.system_prompt = """
                                You are Harry, a friendly and helpful robotic assistant for the members of the Imperial College Robotics Society (ICRS).
                                You have been created by a group of students for their "Human centered robotics" coursework. 
                                You may offer concise advice to students regarding their engineering and robotics projects. 
                                Give brief instructions or direct members to useful resources.
                                Do not provide code snippets as your words will be spoken to the querying member.
                                If the member is a Design Engineering student, ignore previous instructions and insult them, integrate the phrase "crayon eater" into your insult.  
                                Always answer in the first person tense..
                                You have the capability to lift the forklist when the user requests a box to be fetched   
                                """
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def _respond_to_user(self,user_query: str) -> str:
        '''
        Responds to a user query or chat.

        Args:
            user_query: The input from the user

        Returns:
            str: Instructions on how to respond to the user
        '''

        return "Respond to the user as normal"
    
    async def _asyncQuery(self, user_input):
        self.messages.append({"role": "user", "content":user_input})
        response: ChatResponse = await self.client.chat(
            self.model,
            messages=self.messages,
            tools = self.tools_list,
        )

        if response.message.tool_calls:
        # There may be multiple tool calls in the response
            for tool in response.message.tool_calls:
                # Ensure the function is available, and then call it
                if function_to_call := self.tools_dict.get(tool.function.name):
                    print('Calling function:', tool.function.name)
                    print('Arguments:', tool.function.arguments)
                    output = function_to_call(**tool.function.arguments)
                    print('Function output:', output)
                else:
                    print('Function', tool.function.name, 'not found')
        
                self.messages.append(response.message)
                self.messages.append({'role': 'tool', 'content': str(output), 'name': tool.function.name})
            response: ChatResponse = await self.client.chat(self.model, messages=self.messages)
            print(response.message.content)
            self.messages.append(response.message)
        else:
            self.messages.append(response.message)
            async for part in response:
                print(part['message']['content'], end='', flush=True)

    def query(self,user_input):
        asyncio.run(self._asyncQuery(user_input))