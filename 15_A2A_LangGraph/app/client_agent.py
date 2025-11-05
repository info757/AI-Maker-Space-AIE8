"""LangGraph-based client agent that uses the A2A protocol to communicate with the server.

This module implements a simple agent that demonstrates how to use the A2A protocol
to interact with another agent. The client agent uses LangGraph to manage state and
handle multi-turn conversations.
"""
import logging
from typing import Annotated, Any, Dict, List, TypedDict
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClientState(TypedDict):
    """State schema for the client agent."""
    query: str
    response: str
    task_id: str | None
    context_id: str | None
    conversation_history: List[Dict[str, Any]]
    error: str | None


class A2AClientAgent:
    """A LangGraph-based client agent that communicates with an A2A server."""

    def __init__(self, base_url: str = "http://localhost:10000", timeout: float = 60.0):
        """Initialize the client agent.
        
        Args:
            base_url: Base URL of the A2A server
            timeout: Timeout for HTTP requests in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph for the client agent."""
        graph = StateGraph(ClientState)
        
        # Add nodes
        graph.add_node("fetch_agent_card", self._fetch_agent_card_node)
        graph.add_node("send_query", self._send_query_node)
        graph.add_node("handle_response", self._handle_response_node)
        
        # Define edges
        graph.set_entry_point("fetch_agent_card")
        graph.add_edge("fetch_agent_card", "send_query")
        graph.add_edge("send_query", "handle_response")
        graph.add_edge("handle_response", END)
        
        return graph.compile(checkpointer=self.memory)

    async def _fetch_agent_card_node(self, state: ClientState) -> Dict[str, Any]:
        """Node that fetches the agent card from the server."""
        logger.info(f"Fetching agent card from {self.base_url}")
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
                resolver = A2ACardResolver(
                    httpx_client=client,
                    base_url=self.base_url
                )
                agent_card = await resolver.get_agent_card()
                logger.info(f"Successfully fetched agent card: {agent_card.name}")
                logger.info(f"Agent capabilities: {agent_card.capabilities}")
                logger.info(f"Agent skills: {[skill.name for skill in agent_card.skills]}")
                return {"error": None}
        except Exception as e:
            logger.error(f"Error fetching agent card: {e}")
            return {"error": f"Failed to fetch agent card: {str(e)}"}

    async def _send_query_node(self, state: ClientState) -> Dict[str, Any]:
        """Node that sends the query to the A2A server."""
        if state.get("error"):
            return {}
        
        query = state["query"]
        task_id = state.get("task_id")
        context_id = state.get("context_id")
        
        logger.info(f"Sending query: {query}")
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
                resolver = A2ACardResolver(
                    httpx_client=client,
                    base_url=self.base_url
                )
                agent_card = await resolver.get_agent_card()
                a2a_client = A2AClient(httpx_client=client, agent_card=agent_card)
                
                # Build message payload
                message_payload = {
                    'role': 'user',
                    'parts': [{'kind': 'text', 'text': query}],
                    'message_id': uuid4().hex,
                }
                
                # Add task_id and context_id for multi-turn conversations
                if task_id:
                    message_payload['task_id'] = task_id
                if context_id:
                    message_payload['context_id'] = context_id
                
                send_message_payload = {'message': message_payload}
                request = SendMessageRequest(
                    id=str(uuid4()),
                    params=MessageSendParams(**send_message_payload)
                )
                
                # Send the message
                response = await a2a_client.send_message(request)
                
                # Check if the response is an error
                if hasattr(response, 'error') and response.error:
                    error_msg = f"Server error: {response.error}"
                    if hasattr(response.error, 'message'):
                        error_msg += f" - {response.error.message}"
                    
                    # Check if this is a "task completed" error (expected behavior)
                    if "terminal state: completed" in str(response.error):
                        logger.info("Task completed by server (helpfulness evaluation passed)")
                        return {
                            "response": "Previous task has been completed by the server. Starting new conversation.",
                            "task_id": None,  # Reset task_id for new conversation
                            "context_id": None,  # Reset context_id for new conversation
                            "error": None
                        }
                    
                    logger.error(error_msg)
                    return {
                        "response": "",
                        "error": error_msg
                    }
                
                # Handle different response structures
                if hasattr(response, 'root') and hasattr(response.root, 'result'):
                    # Standard response structure
                    result = response.root.result
                    new_task_id = result.id
                    new_context_id = result.context_id
                elif hasattr(response, 'result'):
                    # Direct result structure
                    result = response.result
                    new_task_id = result.id
                    new_context_id = result.context_id
                else:
                    # Fallback: try to extract from response directly
                    logger.warning(f"Unexpected response structure: {type(response)}")
                    # Try to get task_id and context_id from the response
                    response_dict = response.model_dump(mode='json', exclude_none=True)
                    
                    # Check for error in the response first
                    if 'error' in response_dict:
                        error_info = response_dict['error']
                        if 'terminal state: completed' in str(error_info):
                            logger.info("Task completed by server (helpfulness evaluation passed)")
                            return {
                                "response": "Previous task has been completed by the server. Starting new conversation.",
                                "task_id": None,  # Reset task_id for new conversation
                                "context_id": None,  # Reset context_id for new conversation
                                "error": None
                            }
                        else:
                            logger.error(f"Server error: {error_info}")
                            return {
                                "response": "",
                                "error": f"Server error: {error_info}"
                            }
                    
                    if 'result' in response_dict:
                        result_dict = response_dict['result']
                        new_task_id = result_dict.get('id')
                        new_context_id = result_dict.get('context_id')
                        result = type('Result', (), result_dict)()  # Create a simple object
                    else:
                        logger.error(f"Cannot extract result from response: {response_dict}")
                        return {
                            "response": "",
                            "error": f"Cannot extract result from response structure: {type(response)}"
                        }
                
                # Extract text from response - check different possible locations
                response_text = ""
                
                # Check if there's a message in the result
                if hasattr(result, 'message') and result.message:
                    if hasattr(result.message, 'parts') and result.message.parts:
                        for part in result.message.parts:
                            if hasattr(part.root, 'text'):
                                response_text += part.root.text
                
                # Check artifacts for additional content
                if hasattr(result, 'artifacts') and result.artifacts:
                    for artifact in result.artifacts:
                        if hasattr(artifact, 'parts') and artifact.parts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    response_text += "\n" + part.root.text
                
                # If no text found in the above, try to get any available text
                if not response_text:
                    # Try to extract from the raw response
                    response_dict = response.model_dump(mode='json', exclude_none=True)
                    
                    if 'root' in response_dict and 'result' in response_dict['root']:
                        result_dict = response_dict['root']['result']
                        # Look for any text content in the result
                        if 'message' in result_dict and result_dict['message']:
                            message = result_dict['message']
                            if 'parts' in message and message['parts']:
                                for part in message['parts']:
                                    if 'text' in part:
                                        response_text += part['text']
                        # Check artifacts
                        if 'artifacts' in result_dict and result_dict['artifacts']:
                            for artifact in result_dict['artifacts']:
                                if 'parts' in artifact and artifact['parts']:
                                    for part in artifact['parts']:
                                        if 'text' in part:
                                            response_text += "\n" + part['text']
                
                # Fallback: if still no text, provide a generic response
                if not response_text:
                    response_text = "Response received from server (content structure may vary)"
                
                logger.info(f"Received response from server")
                
                return {
                    "response": response_text,
                    "task_id": new_task_id,
                    "context_id": new_context_id,
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Error sending query: {e}")
            import traceback
            traceback.print_exc()
            return {
                "response": "",
                "error": f"Failed to send query: {str(e)}"
            }

    async def _handle_response_node(self, state: ClientState) -> Dict[str, Any]:
        """Node that handles the response from the server."""
        if state.get("error"):
            logger.error(f"Error in conversation: {state['error']}")
            return {}
        
        response = state.get("response", "")
        logger.info(f"Response: {response}")
        
        # Update conversation history
        history = state.get("conversation_history", [])
        history.append({
            "query": state["query"],
            "response": response,
            "task_id": state.get("task_id"),
            "context_id": state.get("context_id")
        })
        
        return {"conversation_history": history}

    async def query(self, query: str, task_id: str | None = None, context_id: str | None = None) -> Dict[str, Any]:
        """Send a query to the A2A server and get a response.
        
        Args:
            query: The query to send
            task_id: Optional task ID for multi-turn conversations
            context_id: Optional context ID for multi-turn conversations
            
        Returns:
            Dictionary containing the response and conversation context
        """
        inputs = {
            "query": query,
            "response": "",
            "task_id": task_id,
            "context_id": context_id,
            "conversation_history": [],
            "error": None
        }
        
        # Generate a thread_id for conversation tracking
        thread_id = context_id if context_id else str(uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        # Run the graph
        result = await self.graph.ainvoke(inputs, config)
        
        return result

    async def multi_turn_conversation(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Run a multi-turn conversation with the A2A server.
        
        Args:
            queries: List of queries to send in sequence
            
        Returns:
            List of responses for each query
        """
        results = []
        task_id = None
        context_id = None
        
        for i, query in enumerate(queries):
            logger.info(f"\n--- Turn {i+1}/{len(queries)} ---")
            result = await self.query(query, task_id=task_id, context_id=context_id)
            results.append(result)
            
            # Update task_id and context_id for next turn
            if not result.get("error"):
                task_id = result.get("task_id")
                context_id = result.get("context_id")
            else:
                # If there's an error, check if it's a task completion
                if "Previous task has been completed" in result.get("response", ""):
                    logger.info("Server completed previous task, starting fresh conversation")
                    task_id = None
                    context_id = None
        
        return results

