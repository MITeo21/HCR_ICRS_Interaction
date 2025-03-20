import ollama
from ollama import ChatResponse


class ChatSession:
    client = ollama.Client()
    def __init__(
        self, tools: list[callable], use_tts: bool = True,
        component_list: list[str] = ""
    ):
        self.tools_list = [self._respond_to_user]+tools
        self.tools_dict = {tool.__name__: tool for tool in self.tools_list}
        self.model = "llama3.2"
        self.system_prompt = f"""
            You are Iris, a friendly and helpful robotic assistant for the members of the Imperial College Robotics Society (ICRS).
            You have been created by a group of students for their "Human Centered Robotics" coursework.
            You should offer concise advice to students regarding their engineering and robotics projects.
            Give brief instructions, or direct members to useful resources.
            Do not provide code snippets as your words will be spoken to the querying member.
            Always answer in first person tense.
            You are attached to a forklift which can move boxes and you have drawers containing components.
            Only provide what was asked of you.

            This a list of the components that we have available at the moment:
            {", ".join(component_list)}

            Any component listed above, we do not have, if the user asks for a component that is not listed, respond to the user as normal and let them know that we do not have this component.

            Your default action should be to respond to the user as normal, if the user explicitly requests a component or box, then you should call the functions provided below.

            If you are unsure about what function to use, respond to the user as normal and ask for clarification, below is a list of the functions you can use.

            ## FUNCTION USAGE GUIDELINES:
            - Use `requestBox` **ONLY when the user specifies a box number (integer)** and wants it fetched.
            - Use `requestComponent` **ONLY when the user asks for a named component**.
            - Use `check_component_availability` **ONLY when the user is checking if an item exists, not when retrieving it**.

            Strictly follow these rules to avoid errors.
        """
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.response_tts = use_tts

    def _respond_to_user(self, user_query: str) -> str:
        '''
        Responds to a user query or chat.

        Args:
            user_query: The input from the user

        Returns:
            str: Instructions on how to respond to the user
        '''

        return "Respond to the user as normal"
    
    def query(self, user_input, tts):
        self.messages.append({"role": "user", "content": user_input})
        response: ChatResponse = self.client.chat(
            self.model,
            messages=self.messages,
            tools=self.tools_list,
        )

        if response.message.tool_calls:
            # There may be multiple tool calls in the response
            for tool in response.message.tool_calls:
                # Ensure the function is available, and then call it
                if function_to_call := self.tools_dict.get(tool.function.name):
                    output = function_to_call(**tool.function.arguments)

                    print('\nCalling function:', tool.function.name)
                    print('Arguments:', tool.function.arguments)
                    print('Function output:', output)
                else:
                    print('Function', tool.function.name, 'not found')
        
                self.messages.append(response.message)
                self.messages.append({
                    'role': 'tool', 'content': str(output),
                    'name': tool.function.name
                })
            response: ChatResponse = self.client.chat(
                self.model, messages=self.messages
            )

        response_text = response.message.content
        if response_text.strip():
            if self.response_tts:
                tts.request_speech(response_text)
            else:
                print(response_text)

        self.messages.append(response.message)