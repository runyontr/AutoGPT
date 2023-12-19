from forge.sdk import (
    Agent,
    AgentDB,
    chat_completion_request,
    ForgeLogger,
    PromptEngine,
    Step,
    StepRequestBody,
    Task,
    TaskRequestBody,
    Workspace,
)

import json
import pprint
import logging
import time

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

from forge.actions import ActionRegister


model = "gpt-4"

LOG = ForgeLogger(__name__)

debug = True

class ForgeAgent(Agent):
    """
    The goal of the Forge is to take care of the boilerplate code, so you can focus on
    agent design.

    There is a great paper surveying the agent landscape: https://arxiv.org/abs/2308.11432
    Which I would highly recommend reading as it will help you understand the possabilities.

    Here is a summary of the key components of an agent:

    Anatomy of an agent:
         - Profile
         - Memory
         - Planning
         - Action

    Profile:

    Agents typically perform a task by assuming specific roles. For example, a teacher,
    a coder, a planner etc. In using the profile in the llm prompt it has been shown to
    improve the quality of the output. https://arxiv.org/abs/2305.14688

    Additionally, based on the profile selected, the agent could be configured to use a
    different llm. The possibilities are endless and the profile can be selected
    dynamically based on the task at hand.

    Memory:

    Memory is critical for the agent to accumulate experiences, self-evolve, and behave
    in a more consistent, reasonable, and effective manner. There are many approaches to
    memory. However, some thoughts: there is long term and short term or working memory.
    You may want different approaches for each. There has also been work exploring the
    idea of memory reflection, which is the ability to assess its memories and re-evaluate
    them. For example, condensing short term memories into long term memories.

    Planning:

    When humans face a complex task, they first break it down into simple subtasks and then
    solve each subtask one by one. The planning module empowers LLM-based agents with the ability
    to think and plan for solving complex tasks, which makes the agent more comprehensive,
    powerful, and reliable. The two key methods to consider are: Planning with feedback and planning
    without feedback.

    Action:

    Actions translate the agent's decisions into specific outcomes. For example, if the agent
    decides to write a file, the action would be to write the file. There are many approaches you
    could implement actions.

    The Forge has a basic module for each of these areas. However, you are free to implement your own.
    This is just a starting point.
    """

    def __init__(self, database: AgentDB, workspace: Workspace):
        """
        The database is used to store tasks, steps and artifact metadata. The workspace is used to
        store artifacts. The workspace is a directory on the file system.

        Feel free to create subclasses of the database and workspace to implement your own storage
        """
        super().__init__(database, workspace)
        # self.memstore = ChromaMemStore("agbenchmark_config/workspace/memory")
        self.abilities = ActionRegister(self)

    async def create_task(self, task_request: TaskRequestBody) -> Task:
        """
        The agent protocol, which is the core of the Forge, works by creating a task and then
        executing steps for that task. This method is called when the agent is asked to create
        a task.

        We are hooking into function to add a custom log message. Though you can do anything you
        want here.
        """
        task = await super().create_task(task_request)
        LOG.info(
            f"📦 Task created: {task.task_id} input: {task.input[:40]}{'...' if len(task.input) > 40 else ''}"
        )
        return task

    async def execute_step(self, task_id: str, step_request: StepRequestBody) -> Step:
        """
        For a tutorial on how to add your own logic please see the offical tutorial series:
        https://aiedge.medium.com/autogpt-forge-e3de53cc58ec

        The agent protocol, which is the core of the Forge, works by creating a task and then
        executing steps for that task. This method is called when the agent is asked to execute
        a step.

        The task that is created contains an input string, for the benchmarks this is the task
        the agent has been asked to solve and additional input, which is a dictionary and
        could contain anything.

        If you want to get the task use:

        ```
        task = await self.db.get_task(task_id)
        ```

        The step request body is essentially the same as the task request and contains an input
        string, for the benchmarks this is the task the agent has been asked to solve and
        additional input, which is a dictionary and could contain anything.

        You need to implement logic that will take in this step input and output the completed step
        as a step object. You can do everything in a single step or you can break it down into
        multiple steps. Returning a request to continue in the step output, the user can then decide
        if they want the agent to continue or not.
        """
        # Firstly we get the task this step is for so we can access the task input
        task = await self.db.get_task(task_id)
        # steps = await self.db.
        LOG.debug(f"Step Request: { step_request }")
        if step_request.input is None:
            step_request.input = task.input
        LOG.debug(f"Running Step for Task { task.task_id }")

        messages = None
        try:
            messages = await self.db.get_chat_history(task_id)
            if debug:
                LOG.info(f"Previous Messages {messages}")
        except Exception as e:
            logging.exception(f"Unable to get chat history from database: {e}")
            LOG.error(f"Unable to get chat history: {e}")
        
        actions = None
        try:
            actions = await self.db.get_action_history(task_id)
            if debug:
                LOG.debug(f"Previous actions FOUND!!!{actions}")
        except Exception as e:
            logging.exception(f"Unable to get previous actions: {e}")
            LOG.error(f"Unable to get actions history: {e}")

        # prompt_engine = PromptEngine("gpt-3.5-turbo-16k")
        prompt_engine = PromptEngine(model)

        # set best practices:
        best_practices = [
                    "File operations should all be done in the local directory when possible.  Don't base file paths off of the root directory.",
                    "When possible, use the abilities to validate the task was completed successfully",
                    "If you're not making progress on the task like you expect, use your abilities to debug the problem",
                    "If nothing is working, return the finish ability and provide an explination of what your assessment is of why the task cannot be completed."
                ]

        if not messages:
            # Initialize the PromptEngine with the "gpt-3.5-turbo" model

            # Load the system and task prompts
            system_prompt = prompt_engine.load_prompt("system-format")

            # Initialize the messages list with the system prompt
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            # Define the task parameters
            task_kwargs = {
                "task": step_request.input,
                # "abilities": self.abilities,
                "actions": self.abilities.list_abilities_for_prompt(),
                "expert": "agent",
                "best_practices": best_practices,
            }
            if actions:
                # remove any actions that have a "finish" name so that we can do multiple
                # commands within the same workspace
                actions = [a for a in actions if a['name'] != 'finish']
                task_kwargs['previous_actions'] = actions

            # Load the task prompt with the defined task parameters
            task_prompt = prompt_engine.load_prompt("task-step", **task_kwargs)
            if debug:
                LOG.debug(f"TASK PROMPT:\n\n{task_prompt}")
            # Append the task prompt to the messages list
            messages.append({"role": "user", "content": task_prompt})
            msgs = await self.db.add_chat_history(task_id, messages)
            if debug:
                LOG.info(f"\t self.db.add_chat_history:  { msgs } ")

        else:
            # Define the task parameters
            task_kwargs = {
                "task": step_request.input,
                "actions": self.abilities.list_abilities_for_prompt(),
                "best_practices": best_practices,
            }

            if actions:
                task_kwargs['previous_actions'] = actions
            # Load the task prompt with the defined task parameters
            task_prompt = prompt_engine.load_prompt("task-step", **task_kwargs)
            if debug:
                LOG.debug(f"TASK PROMPT:\n\n{task_prompt}")
            messages.append({"role": "user", "content": task_prompt})
            msg = await self.db.add_chat_message(task_id, "user", step_request.input)

        # Define the parameters for the chat completion request
        # while True:
        answer = None
        try:
            chat_completion_kwargs = {
                "messages": messages,
                # "model": "gpt-3.5-turbo-16k",
                "model": model,
            }

            # Make the chat completion request and parse the response
            # if debug:
                # LOG.info(pprint.pformat("Prompt being sent to gpt-3.5"))
                # LOG.info(pprint.pformat(chat_completion_kwargs))
            if model == "gpt-4":
                pprint.pprint(f"Waiting 60 seconds for GPT-4 token limite to refresh")
                time.sleep(60)
            chat_response = await chat_completion_request(**chat_completion_kwargs)
            # if debug:
                # LOG.info(pprint.pformat("response from gpt-3.5"))
                # LOG.info(pprint.pformat(chat_response))
            answer = json.loads(chat_response["choices"][0]["message"]["content"])


            # Log the answer for debugging purposes
            if debug:
                LOG.info(f"LLM Response:\n\n{answer}")

        except json.JSONDecodeError as e:
            # Handle JSON decoding errors
            LOG.error(f"Unable to decode chat response: {chat_response}")
            logging.exception(f"EUnable to decode chat response: {e}")
        except Exception as e:
            # Handle other exceptions
            LOG.error(f"Unable to generate chat response: {e}")
            logging.exception(f"Unable to generate chat response: {e}")
        if answer is None:
            LOG.info(f"Error getting response from server. Sleeping 30 seconds and trying again.")
            time.sleep(30)
            return self.execute_step(task_id, step_request)
        # Check if the task is complete
        if (answer.get('ability', {}).get('name', '') == 'finish'):
            LOG.info(f"Chat thinks the task is complete.  Returning")
            # Set the step output to the "speak" part of the answer
            step = await self.db.create_step(
                task_id=task_id, 
                input=step_request, 
                additional_input= {
                    "name": "finish",
                    "output": answer["reasoning"]["speak"],
                },
                is_last=True,
            )

            # Log the message
            if debug:
                LOG.info(f"\t✅ Final Step completed: {step.step_id} input: {step_request.input[:19]}")
            # msg = await self.db.add_chat_message(task_id, "assistant", answer["reasoning"]["speak"])
            # self.db.update_step(task_id=tas)
            # Return the completed step
            return step
        if debug:
            LOG.debug(f" Requested Ability: {answer.get('action', {}).get('name', '') }")
        if answer.get('action', {}).get('name', '') in self.abilities.list_abilities():
            try:
                # Extract the ability from the answer
                selected_action = answer["action"]
                if debug:
                    LOG.info(f"Chat Engine is suggesting to do the following action: { selected_action['name']} with paratmers { selected_action['args']}")
                    
                step = await self.db.create_step(
                    task_id=task_id, input=step_request,                    
                )
                step.output = answer["thoughts"]["reasoning"]
                step.input = step_request.input
                step.name = selected_action['name']
                
                # Run the ability and get the output
                # We don't actually use the output in this example
                if debug:
                    LOG.info(pprint.pformat(f"Running action {selected_action['name']} with args { selected_action['args']}"))
                # if ability['name'] == "finish":
                #     self.db.update_step(task_id=task_id, step_id=step.step_id, status=)
                output = await self.abilities.run_action(
                    task_id, selected_action["name"], **selected_action["args"]
                )
                action = await self.db.create_action( task_id,
                                                      selected_action["name"], 
                                                      selected_action["args"], 
                                                      reason=answer["thoughts"]["reasoning"],
                                                      output=f"{output}")
                LOG.info(f"\t✅ Created Action { action.action_id} for step {step.step_id } under task {task.task_id}")
                
                if debug:
                    LOG.debug(f"Output of task: { output } ")
                # step.name = action["name"]
                step.input = step_request.input
                step.output = f"{output}"

                # Log the message
                if debug:
                    LOG.info(f"\t✅ Intermediate Step completed: {step.step_id} input: {step.input[:19]}")
                return step
            except Exception as e:
                # Handle any exceptions
                LOG.error(f"Unable to run ability: {e}")
                logging.exception(f"Error running ability: {e}")
                step = await self.db.create_step(
                    task_id=task_id, input=step_request
                )
                step.output = "Asked for bad action"
                action = await self.db.create_action( task_id,
                                                      selected_action["name"], 
                                                      selected_action["args"], 
                                                      reason=answer["thoughts"]["reasoning"],
                                                      output=f"{ e }")
                LOG.info(f"\t✅ Created Action { action.action_id} for step {step.step_id } under task {task.task_id}")
                
                return step
        LOG.error(f"asking for an action that didn't exist {answer.get('ability', {}).get('name', '')}.  Lets return and try this again")
        step = await self.db.create_step(
                    task_id=task_id, input=step_request,
                )
        step.output = "Asked for bad action"
        step.input = step_request.input
        step.name = "error"
        return step
       