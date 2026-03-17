import chainlit as cl
import dotenv

dotenv.load_dotenv()

# additional imports
from agents import Runner
from nutrition_agent import nutrition_agent
from openai.types.responses import ResponseTextDeltaEvent


# to make the function below work we need the chainlit tag
@cl.on_message
async def on_message(message: cl.Message):
    """
    # we pass our input as a message to the nutrition agent:
    result = await Runner.run(nutrition_agent, message.content)
    # we change the received message from prior example to the actual output of the nutrition agent
    # await cl.Message(content=f"Received: {message.content}").send() to the following code
    await cl.Message(content=result.final_output).send()
    """

    result = Runner.run_streamed(
        nutrition_agent,
        message.content,
    )

    # streaming the result to chainlit, such that all the message is shown on screen as soon as new content comes up
    # creating a chainlit message variable to store the output message:
    msg = cl.Message(content="")
    # creating a loop to add the output stream one by one to the above created message.
    async for event in result.stream_events():
        # Stream final message text to screen word by word to ui.
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            # we only get this far if the triggered event is a raw response type and the event.data is of type ResponseTextDeltaEvent
            # once the above conditions are fulfilled, we can be sure that this token we receive is a response from the agent
            await msg.stream_token(token=event.data.delta)
            # here we print it to the console for easy debugging.
            print(event.data.delta, end="", flush=True)

        # we catch toolcalls here:
        elif (
            event.type == "raw_response_event"
            and hasattr(event.data, "item")
            and hasattr(event.data.item, "type")
            and event.data.item.type == "function_call"
            and len(event.data.item.arguments) > 0
        ):
            # once we are clear i.e differentiated between a message and tool call, then we move forward to using steps in chainlit
            # using this will show us individual steps that our agent uses to find our answers.
            with cl.Step(name=f"{event.data.item.name}", type="tool") as step:
                step.input = event.data.item.arguments
                print(
                    f"\nTool call: {
                        event.data.item.name} with args: {
                        event.data.item.arguments}"
                )
    # we add the output to the message as we are not waiting for full output from the nutrition agent.
    await msg.update()