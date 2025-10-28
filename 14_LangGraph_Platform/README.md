<p align = "center" draggable=”false” ><img src="https://github.com/AI-Maker-Space/LLM-Dev-101/assets/37101144/d1343317-fa2f-41e1-8af1-1dbb18399719" 
     width="200px"
     height="auto"/>
</p>

## <h1 align="center" id="heading">Session 14: Build & Serve Agentic Graphs with LangGraph</h1>

| 🤓 Pre-work | 📰 Session Sheet | ⏺️ Recording     | 🖼️ Slides        | 👨‍💻 Repo         | 📝 Homework      | 📁 Feedback       |
|:-----------------|:-----------------|:-----------------|:-----------------|:-----------------|:-----------------|:-----------------|


# Build 🏗️

Run the repository and complete the following:

- 🤝 Breakout Room Part #1 — Building and serving your LangGraph Agent Graph
  - Task 1: Getting Dependencies & Environment
    - Configure `.env` (OpenAI, Tavily, optional LangSmith)
  - Task 2: Serve the Graph Locally
    - `uv run langgraph dev` (API on http://localhost:2024)
  - Task 3: Call the API from a different terminal
    - `uv run test_served_graph.py` (sync SDK example)
  - Task 4: Explore assistants (from `langgraph.json`)
    - `agent` → `simple_agent` (tool-using agent)
    - `agent_helpful` → `agent_with_helpfulness` (separate helpfulness node)

- 🤝 Breakout Room Part #2 — Using LangGraph Studio to visualize the graph
  - Task 1: Open Studio while the server is running
    - https://smith.langchain.com/studio?baseUrl=http://localhost:2024
  - Task 2: Visualize & Stream
    - Start a run and observe node-by-node updates
  - Task 3: Compare Flows
    - Contrast `agent` vs `agent_helpful` (tool calls vs helpfulness decision)

## Activities and Questions 🏗️ &❓

#### ❓ Question 1:

Compare the `agent` and `agent_helpful` assistants defined in `langgraph.json`. Where does the helpfulness evaluator fit in the graph, and under what condition should execution route back to the agent vs. terminate?

##### ✅ Answer:

**Comparison of `agent` vs `agent_helpful` assistants:**

The key difference is in their graph structure and execution flow:

**`agent` (simple_agent):**
- **Graph Flow**: `agent` → `action` (if tool calls) → `agent` → END
- **Routing Logic**: Only checks if the last message contains tool calls
- **Termination**: Ends immediately after the agent responds (if no tool calls needed)

**`agent_helpful` (agent_with_helpfulness):**
- **Graph Flow**: `agent` → `action` (if tool calls) → `agent` → `helpfulness` → `agent` (if not helpful) → END
- **Routing Logic**: After agent responds, routes to helpfulness evaluator instead of ending
- **Helpfulness Evaluator**: Uses a separate LLM call to evaluate if the response adequately addresses the original query
- **Loop Control**: Has a safety limit (10 messages) to prevent infinite loops

**Where the helpfulness evaluator fits:**
The helpfulness evaluator sits between the agent's response and the final termination. It acts as a quality gate that:
1. Compares the agent's final response against the original user query
2. Uses a separate model (gpt-4.1-mini) to make a Y/N decision
3. Routes back to the agent if the response is deemed unhelpful (N)
4. Terminates if the response is helpful (Y) or if the loop limit is exceeded

**Execution routing conditions:**
- **Route back to agent**: When helpfulness evaluator returns "N" (not helpful)
- **Terminate**: When helpfulness evaluator returns "Y" (helpful) OR when loop limit (10 messages) is exceeded

#### 🏗️ Activity #1 Debugging A Graph

Select the `agent_with_helpfulness` and set one or more interrupts (at least one `Before` and one `After`). Try changing values and continuing the turn. 

#### ❓ Question 2:

What are your thoughts on when you would use a Before interrupt vs. an After interrupt?

##### ✅ Answer:

**Before Interrupts** are most useful when you want to:

1. **Inspect and validate inputs** before a node processes them
   - Check if the data format is correct
   - Verify that required fields are present
   - Debug why a node might be receiving unexpected data

2. **Modify inputs** before expensive operations
   - Clean or transform data before processing
   - Add missing context or parameters
   - Prevent errors by fixing data issues

3. **Debug node failures** by examining what caused them
   - See the exact state that led to an error
   - Understand the data flow before a problematic node

**After Interrupts** are most useful when you want to:

1. **Inspect and validate outputs** after a node completes
   - Verify that the node produced expected results
   - Check the quality or format of outputs
   - Debug why downstream nodes might be failing

2. **Modify outputs** before they're passed to the next node
   - Clean up or reformat responses
   - Add additional context or metadata
   - Override decisions (like changing a "N" to "Y" in helpfulness evaluation)

3. **Debug unexpected behavior** by examining what a node actually produced
   - See if the node's logic worked as expected
   - Understand why the graph is taking a particular path

**Practical Example with `agent_with_helpfulness`:**
- **Before `helpfulness`**: Inspect the query and response being evaluated
- **After `helpfulness`**: See the Y/N decision and potentially override it
- **Before `agent`**: Check what context the agent will work with
- **After `agent`**: Review the agent's response and potentially modify it

**Key Insight**: Before interrupts help you debug **input problems**, while After interrupts help you debug **output problems** or **modify the execution flow**.



<details>
<summary>🚧 Advanced Build 🚧 (OPTIONAL - <i>open this section for the requirements</i>)</summary>

- Create and deploy a locally hosted MCP server with FastMCP.
- Extend your tools in `tools.py` to allow your LangGraph to consume the MCP Server.
</details>

# Ship 🚢

- Running local server (`langgraph dev`)
- Short demo showing both assistants responding

# Share 🚀
- Walk through your graph in Studio
- Share 3 lessons learned and 3 lessons not learned

# Main Homework Assignment

Follow these steps to prepare and submit your homework assignment:
1. Create a branch of your `AIE8` repo to track your changes. Example command: `git checkout -b s14-assignment`
2. Complete the Tasks listed in the Breakout Room sections of `Build 🏗️`
3. Complete the activities and questions in `Activities and Questions 🏗️ &❓` by editing the file and replacing "_(enter answer here)_" with your responses
3. Commit, and push your completed notebook to your `origin` repository. _NOTE: Do not merge it into your main branch._
4. Record a Loom video reviewing the content of your completed notebook
5. Make sure to include all of the following on your Homework Submission Form:
    + The GitHub URL to the `README.md` file _on your assignment branch (not main)_
    + The URL to your Loom Video
    + Your Three Lessons Learned/Not Yet Learned
    + The URLs to any social media posts (LinkedIn, X, Discord, etc.) ⬅️ _easy Extra Credit points!_


### OPTIONAL: 🚧 Advanced Build Assignment 🚧
<details>
  <summary>(<i>Open this section for the submission instructions.</i>)</summary>

Follow these steps to prepare and submit your homework assignment:
1. Create a branch of your `AIE8` repo to track your changes. Example command: `git checkout -b s14-assignment`
2. Create your MCP server
3. Add it to the existing graph's tools
4. Deploy it ***locally***
5. Validate the graph uses the MCP server's tools
6. Commit, and push your changes to your `origin` repository. _NOTE: Do not merge it into your main branch._
7. Record a Loom video reviewing the content of your completed notebook.
8. Make sure to include all of the following on your Homework Submission Form:
    + The GitHub URL to the notebook you created for the Advanced Build Assignment _on your assignment branch_
    + The URL to your Loom Video
    + Your Three Lessons Learned/Not Yet Learned
    + The URLs to any social media posts (LinkedIn, X, Discord, etc.) ⬅️ _easy Extra Credit points!_

</details>
