"""
Integration Guide for Enhanced Chat Handler

This module shows how to integrate the enhanced chat handler with the existing CS 15 Tutor system.
"""

# Import the enhanced handler
from enhanced_chat_handler import EnhancedChatHandler

# Initialize the enhanced handler (do this once at startup)
enhanced_handler = EnhancedChatHandler()

def integrate_with_existing_chat_handler():
    """
    Example of how to integrate with the existing chat_handler function in index.py
    """
    
    # This would replace the existing chat_handler function in index.py
    def enhanced_chat_handler_existing():
        """
        Enhanced version of the existing chat_handler function
        """
        request_start_time = time.time()
        
        try:
            # ... existing authentication and validation code ...
            # (Keep all the existing authentication, health points, logging code)
            
            # NEW: Use enhanced processing instead of direct LLM call
            result = enhanced_handler.process_chat_request(
                message=message,
                conversation_id=conversation_id,
                conversation_history=conversations[conversation_id],
                conversation_rag_context=conversation_rag_context[conversation_id],
                utln=utln,
                platform=platform
            )
            
            # Extract response and metadata
            assistant_response = result["response"]
            category = result["category"]
            enhanced_metadata = result["enhanced_metadata"]
            
            # Update conversation history (same as before)
            conversation_history = conversations[conversation_id]
            conversation_history.append({"role": "user", "content": message})
            conversation_history.append({"role": "assistant", "content": assistant_response})
            
            # Calculate response time
            response_time_ms = result["response_time_ms"]
            
            # Log the assistant response (enhanced with category info)
            logging_service.log_assistant_response(
                conversation_id=conversation_id,
                response=assistant_response,
                rag_context=result["rag_context"],
                model_used='4o-mini',
                temperature=0.7,
                response_time_ms=response_time_ms,
                # NEW: Add category information to logging
                category=category,
                enhanced_metadata=enhanced_metadata
            )
            
            # Get updated health status
            health_status = db_manager.get_user_health_status(user_data['id'])
            
            # Return enhanced response
            return jsonify({
                "response": assistant_response,
                "rag_context": result["rag_context"],
                "conversation_id": conversation_id,
                "category": category,  # NEW: Include category in response
                "enhanced_metadata": enhanced_metadata,  # NEW: Include enhanced metadata
                "user_info": {
                    "anonymous_id": query_log_result.get('anonymous_id'),
                    "platform": platform,
                    "is_new_conversation": query_log_result.get('is_new_conversation', False)
                },
                "health_status": health_status
            })
            
        except Exception as error:
            print(f"❌ Error processing request: {error}")
            return jsonify({"error": "Sorry, an error occurred while processing your request."}), 500
    
    return enhanced_chat_handler_existing

def integrate_with_streaming_handler():
    """
    Example of how to integrate with the existing chat_handler_stream function
    """
    
    def enhanced_chat_handler_stream():
        """
        Enhanced version of the existing streaming chat handler
        """
        request_start_time = time.time()
        
        # ... existing authentication code ...
        
        def generate_events():
            try:
                # ... existing validation and health point checks ...
                
                # NEW: Use enhanced processing
                result = enhanced_handler.process_chat_request(
                    message=message,
                    conversation_id=conversation_id,
                    conversation_history=conversations[conversation_id],
                    conversation_rag_context=conversation_rag_context[conversation_id],
                    utln=utln,
                    platform=platform
                )
                
                # Extract response and metadata
                assistant_response = result["response"]
                category = result["category"]
                enhanced_metadata = result["enhanced_metadata"]
                
                # Update conversation history
                conversation_history = conversations[conversation_id]
                conversation_history.append({"role": "user", "content": message})
                conversation_history.append({"role": "assistant", "content": assistant_response})
                
                # Calculate response time
                response_time_ms = result["response_time_ms"]
                
                # Log the assistant response
                logging_service.log_assistant_response(
                    conversation_id=conversation_id,
                    response=assistant_response,
                    rag_context=result["rag_context"],
                    model_used='4o-mini',
                    temperature=0.7,
                    response_time_ms=response_time_ms,
                    category=category,
                    enhanced_metadata=enhanced_metadata
                )
                
                # Get updated health status
                health_status = db_manager.get_user_health_status(user_data['id'])
                
                # Send final response with enhanced metadata
                response_data = {
                    "status": "complete", 
                    "response": assistant_response, 
                    "rag_context": result["rag_context"], 
                    "conversation_id": conversation_id,
                    "category": category,  # NEW
                    "enhanced_metadata": enhanced_metadata,  # NEW
                    "user_info": {
                        "anonymous_id": query_log_result.get('anonymous_id'),
                        "platform": platform,
                        "is_new_conversation": query_log_result.get('is_new_conversation', False)
                    },
                    "health_status": health_status
                }
                yield f'data: {json.dumps(response_data)}\n\n'
                
            except Exception as error:
                print(f"❌ Error processing request: {error}")
                yield f'data: {json.dumps({"status": "error", "error": "Sorry, an error occurred while processing your request."})}\n\n'
        
        return Response(
            stream_with_context(generate_events()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    
    return enhanced_chat_handler_stream

def update_logging_service():
    """
    Example of how to update the logging service to handle enhanced metadata
    """
    
    # Add this to your logging_service.py
    def log_assistant_response_enhanced(
        conversation_id: str,
        response: str,
        rag_context: str,
        model_used: str,
        temperature: float,
        response_time_ms: int,
        category: str = None,  # NEW
        enhanced_metadata: dict = None  # NEW
    ):
        """
        Enhanced version of log_assistant_response that includes category and metadata
        """
        # ... existing logging code ...
        
        # NEW: Add category and enhanced metadata to the log
        if category:
            # Log category information
            pass
        
        if enhanced_metadata:
            # Log enhanced metadata (processing stages, quality checks, etc.)
            pass
        
        # ... rest of existing logging code ...

def update_frontend_to_handle_categories():
    """
    Example of how to update the frontend to handle category information
    """
    
    # In your web-app/services/chatApi.ts, update the interface:
    """
    interface ChatResponse {
      response?: string;
      error?: string;
      rag_context?: string;
      conversation_id?: string;
      health_status?: HealthStatus;
      category?: string;  // NEW
      enhanced_metadata?: {  // NEW
        query_category: string;
        processing_stages: string[];
        quality_checks_performed: boolean;
        rag_context_used: boolean;
      };
    }
    """
    
    # In your web-app/hooks/useChat.ts, you can now access category info:
    """
    if (data.response) {
      updateLastMessage(data.response, false);
      
      // NEW: Access category information
      if (data.category) {
        console.log(`Query categorized as: ${data.category}`);
      }
      
      if (data.enhanced_metadata) {
        console.log(`Processing stages: ${data.enhanced_metadata.processing_stages}`);
        console.log(`Quality checks performed: ${data.enhanced_metadata.quality_checks_performed}`);
      }
      
      // Update health status from response
      if (data.health_status) {
        setHealthStatus(data.health_status);
      }
    }
    """

def update_vscode_extension():
    """
    Example of how to update the VS Code extension to handle category information
    """
    
    # In your vscode-extension/src/chatViewProvider.ts, update the message handling:
    """
    case 'response':
        if (isAuthenticated) {
            const loadingMessages = document.querySelectorAll('.message.bot .loading');
            loadingMessages.forEach(msg => {
                if (msg.parentElement) {
                    msg.parentElement.remove();
                }
            });
            
            if (message.error) {
                addMessage(message.error, 'bot');
            } else if (message.response) {
                addMessage(message.response, 'bot');
                
                // NEW: Log category information
                if (message.category) {
                    console.log(`Query categorized as: ${message.category}`);
                }
                
                if (message.enhanced_metadata) {
                    console.log(`Enhanced processing: ${JSON.stringify(message.enhanced_metadata)}`);
                }
            }
            
            // Update health status from response
            if (message.health_status) {
                updateHealthBar(message.health_status);
            }
            
            isLoading = false;
            sendButton.disabled = healthStatus && !healthStatus.can_query;
            chatInput.focus();
        }
        break;
    """

def step_by_step_integration():
    """
    Step-by-step integration guide
    """
    
    print("🚀 Enhanced Chat Handler Integration Guide")
    print("=" * 50)
    
    print("\n📋 Step 1: Add the new modules")
    print("- Copy query_categorization.py to responses-api-server/")
    print("- Copy enhanced_chat_handler.py to responses-api-server/")
    
    print("\n📋 Step 2: Update imports in index.py")
    print("- Add: from enhanced_chat_handler import EnhancedChatHandler")
    print("- Add: enhanced_handler = EnhancedChatHandler()")
    
    print("\n📋 Step 3: Replace the LLM call in chat_handler")
    print("- Replace the generate() call with enhanced_handler.process_chat_request()")
    print("- Update response handling to extract category and metadata")
    
    print("\n📋 Step 4: Update logging service")
    print("- Add category and enhanced_metadata parameters to log_assistant_response")
    print("- Update database schema if needed")
    
    print("\n📋 Step 5: Update frontend interfaces")
    print("- Add category and enhanced_metadata to ChatResponse interface")
    print("- Update message handling in useChat.ts")
    print("- Update VS Code extension message handling")
    
    print("\n📋 Step 6: Test the integration")
    print("- Test with different query types")
    print("- Verify category classification")
    print("- Check quality checking and regeneration")
    print("- Monitor response times and performance")
    
    print("\n✅ Benefits of the enhanced system:")
    print("- Better academic integrity protection")
    print("- More targeted and appropriate responses")
    print("- Quality assurance through automated checking")
    print("- Detailed analytics on query types and processing")
    print("- Automatic regeneration of problematic responses")

if __name__ == "__main__":
    step_by_step_integration() 