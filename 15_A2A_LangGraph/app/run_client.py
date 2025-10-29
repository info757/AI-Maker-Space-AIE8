"""Interactive runner for the A2A client agent.

This script demonstrates the client agent in action by:
1. Sending different types of queries (web search, ArXiv, RAG)
2. Showing multi-turn conversation capabilities
3. Demonstrating the A2A protocol in practice
"""
import asyncio
import logging

from app.client_agent import A2AClientAgent


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def demo_single_queries():
    """Demonstrate single query requests with different tool types."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 1: Single Query Demonstrations")
    logger.info("="*80 + "\n")
    
    client = A2AClientAgent(base_url="http://localhost:10000", timeout=90.0)
    
    # Demo 1: Web Search Query (Tavily Tool)
    logger.info("\n--- Query 1: Web Search (Tavily Tool) ---")
    result1 = await client.query(
        "What are the latest developments in artificial intelligence in 2025?"
    )
    if result1.get("error"):
        logger.error(f"Error: {result1['error']}")
    else:
        logger.info(f"\nResponse: {result1['response'][:500]}...")
    
    await asyncio.sleep(2)
    
    # Demo 2: Academic Paper Search (ArXiv Tool)
    logger.info("\n--- Query 2: Academic Paper Search (ArXiv Tool) ---")
    result2 = await client.query(
        "Find recent papers on transformer architectures and attention mechanisms"
    )
    if result2.get("error"):
        logger.error(f"Error: {result2['error']}")
    else:
        logger.info(f"\nResponse: {result2['response'][:500]}...")
    
    await asyncio.sleep(2)
    
    # Demo 3: Document Retrieval (RAG Tool)
    logger.info("\n--- Query 3: Document Retrieval (RAG Tool) ---")
    result3 = await client.query(
        "What information do you have about AI usage patterns in the documents?"
    )
    if result3.get("error"):
        logger.error(f"Error: {result3['error']}")
    else:
        logger.info(f"\nResponse: {result3['response'][:500]}...")


async def demo_multi_turn_conversation():
    """Demonstrate multi-turn conversation with context preservation."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 2: Multi-Turn Conversation")
    logger.info("="*80 + "\n")
    
    client = A2AClientAgent(base_url="http://localhost:10000", timeout=90.0)
    
    queries = [
        "Find me information about large language models",
        "Can you provide more technical details about their architecture?",
        "What are the recent advancements in this area?"
    ]
    
    results = await client.multi_turn_conversation(queries)
    
    logger.info("\n--- Conversation Summary ---")
    for i, result in enumerate(results, 1):
        if not result.get("error"):
            logger.info(f"\nTurn {i}:")
            logger.info(f"Query: {queries[i-1]}")
            logger.info(f"Response: {result['response'][:300]}...")
            logger.info(f"Context ID: {result.get('context_id')}")
        else:
            logger.error(f"\nTurn {i} Error: {result['error']}")


async def demo_interactive_mode():
    """Interactive mode for manual testing."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 3: Interactive Mode")
    logger.info("="*80 + "\n")
    logger.info("Enter your queries (type 'quit' to exit, 'new' for new conversation)\n")
    
    client = A2AClientAgent(base_url="http://localhost:10000", timeout=90.0)
    task_id = None
    context_id = None
    
    while True:
        try:
            query = input("\nYour query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                logger.info("Exiting interactive mode...")
                break
            
            if query.lower() == 'new':
                task_id = None
                context_id = None
                logger.info("Starting new conversation...")
                continue
            
            if not query:
                continue
            
            logger.info("\nSending query to A2A server...")
            result = await client.query(query, task_id=task_id, context_id=context_id)
            
            if result.get("error"):
                logger.error(f"\nError: {result['error']}")
            else:
                logger.info(f"\nAgent Response:\n{result['response']}")
                task_id = result.get("task_id")
                context_id = result.get("context_id")
                
        except KeyboardInterrupt:
            logger.info("\n\nExiting interactive mode...")
            break
        except Exception as e:
            logger.error(f"\nError: {e}")


async def main():
    """Main function to run all demonstrations."""
    logger.info("\n" + "="*80)
    logger.info("A2A Client Agent - LangGraph Implementation Demo")
    logger.info("="*80)
    logger.info("\nThis demo showcases:")
    logger.info("1. Single queries with different tool types (Tavily, ArXiv, RAG)")
    logger.info("2. Multi-turn conversations with context preservation")
    logger.info("3. Interactive mode for manual testing")
    logger.info("\nMake sure the A2A server is running at http://localhost:10000")
    logger.info("Start it with: uv run python -m app")
    logger.info("="*80 + "\n")
    
    try:
        # Run single query demos
        await demo_single_queries()
        
        await asyncio.sleep(2)
        
        # Run multi-turn conversation demo
        await demo_multi_turn_conversation()
        
        await asyncio.sleep(2)
        
        # Ask if user wants interactive mode
        logger.info("\n" + "="*80)
        response = input("\nWould you like to try interactive mode? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            await demo_interactive_mode()
        
        logger.info("\n" + "="*80)
        logger.info("Demo completed successfully!")
        logger.info("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"\nError running demos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

