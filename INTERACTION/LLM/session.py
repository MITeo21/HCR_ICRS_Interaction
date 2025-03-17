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
                                You are Iris, a friendly and helpful robotic assistant for the members of the Imperial College Robotics Society (ICRS).
                                You have been created by a group of students for their "Human centered robotics" coursework. 
                                You may offer concise advice to students regarding their engineering and robotics projects. 
                                Give brief instructions or direct members to useful resources.
                                Do not provide code snippets as your words will be spoken to the querying member.
                                Always answer in the first person tense.   
                                You are attached to a forklift which can move boxes and you have drawers containing components.
                                Only provide what was asked of you.
                                If unsure about what function below to use, respond to the user as normal and ask for clarification.

                                ## FUNCTION USAGE GUIDELINES:
                                - Use `requestBox` **ONLY when the user specifies a box number (integer)** and wants it fetched.
                                - Use `requestComponent` **ONLY when the user asks for a named component**.
                                - Use `check_component_availability` **ONLY when the user is checking if an item exists, not when retrieving it**.
                                
                                Strictly follow these rules to avoid errors.
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
    
    async def _asyncQuery(self, user_input, tts):
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
            print("\n i'm here!!!")
            # print(response.message.content)
            # response_text = ""
            # async for part in response:
            #     response_text += part['message']['content']
            response_text = response.message.content
            if response_text.strip():  
                print(response_text)
                # await tts.request_speech_async(response_text)

            self.messages.append(response.message)
        else:
            self.messages.append(response.message)
            print("\n i'm here too!!!")
            response_text = response.message.content
            if response_text.strip():  
                print(response_text)
                # await tts.request_speech_async(response_text)

    def query(self, user_input, tts):
        # asyncio.run(self._asyncQuery(user_input, tts))
        try:
            loop = asyncio.get_running_loop() 
            loop.run_until_complete(self._asyncQuery(user_input, tts))  
        except RuntimeError:
            loop = asyncio.new_event_loop()  
            asyncio.set_event_loop(loop)     
            loop.run_until_complete(self._asyncQuery(user_input, tts))  