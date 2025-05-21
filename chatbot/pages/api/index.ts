import { NextApiRequest, NextApiResponse } from "next";
import { OpenAI } from "openai";
import dotenv from "dotenv";
import fs from 'fs';
import path from "path";
import { ChatCompletionMessageParam } from "openai/resources/chat/completions";

dotenv.config({ path: path.resolve(process.cwd(), "../.env") });

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Define an array with your initial keywords
let courseKeywords = ["metrosim", "zap", "gerp", "calcyoulater"];

// identify if a query needs to search through the specs
function isCourseRelated(query: string): boolean {
  // Dynamically create a regex pattern from the array
  const regex = new RegExp(courseKeywords.join("|"), "i");
  const isRelated = regex.test(query);
  console.log("🔍 Query:", query);
  console.log("🎯 Keywords:", courseKeywords);
  console.log("📌 Is course related:", isRelated);
  return isRelated;
}

// Function to load the system prompt
function loadSystemPrompt(): string {
  const promptPath = path.join(process.cwd(), "system-prompt.txt");
  return fs.readFileSync(promptPath, "utf-8");
}

/**
 * Converts a query string into an embedding using OpenAI's API.
 */
async function getQueryEmbedding(query: string): Promise<number[]> {
  const embeddingResponse = await openai.embeddings.create({
    model: "text-embedding-ada-002",
    input: query
  });
  // Extract and return the embedding vector
  return embeddingResponse.data[0].embedding;
}

/**
 * Truncates text to a maximum number of characters
 */
function truncateText(text: string, maxChars: number = 8000): string {
  if (text.length <= maxChars) return text;
  return text.substring(0, maxChars) + "...";
}

/**
 * Retrieves relevant content by sending the query embedding to the Python retrieval service.
 */
async function retrieveContent(query: string): Promise<string> {
  // First, check if the retrieval service is running
  try {
    const healthCheck = await fetch("http://localhost:5050/health");
    if (!healthCheck.ok) {
      throw new Error("Retrieval service is not healthy");
    }
  } catch (error) {
    console.error("❌ Retrieval service health check failed:", error);
    throw new Error("Retrieval service is not available");
  }

  // First, generate an embedding for the query
  const queryEmbedding = await getQueryEmbedding(query);
  
  // Call the Python microservice to search the FAISS index
  const response = await fetch("http://localhost:5050/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ embedding: queryEmbedding, k: 2 }) // Reduced from 3 to 2 results
  });
  
  if (!response.ok) {
    throw new Error("Failed to retrieve context from the retrieval service.");
  }
  
  const data = await response.json();
  // Check if data.results exists and is an array
  if (!data.results || !Array.isArray(data.results)) {
    console.error("Invalid response format from retrieval service:", data);
    throw new Error("Invalid response format from retrieval service");
  }
  // Extract documents from results array, join them, and truncate if necessary
  const combinedText = data.results.map((result: { document: string }) => result.document).join("\n");
  return truncateText(combinedText);
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  // Set headers for streaming response
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Transfer-Encoding', 'chunked');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  try {
    const { message } = req.body;
    let augmentedMessage = message;

    console.log("📝 Processing message:", message);

    // Only retrieve context if the query is course-related
    if (isCourseRelated(message)) {
      console.log("📚 Message is course-related, retrieving context...");
      try {
        const retrievedContext = await retrieveContent(message);
        console.log("📄 Retrieved context length:", retrievedContext.length);
        augmentedMessage = `Context:\n${retrievedContext}\n\nQuestion:\n${message}`;
      } catch (error) {
        console.error("❌ Error retrieving context:", error);
        // Continue with original message if context retrieval fails
      }
    } else {
      console.log("📭 Message is not course-related, skipping retrieval");
    }

    // Load fresh system prompt and initialize conversation history
    const systemPrompt = loadSystemPrompt();
    const conversationHistory: ChatCompletionMessageParam[] = [
      { role: "system", content: systemPrompt },
      { role: "user", content: augmentedMessage }
    ];

    // Create a streaming response
    const stream = await openai.chat.completions.create({
      model: "gpt-4",
      messages: conversationHistory,
      stream: true,
    });

    let fullResponse = '';

    // Process each chunk from the stream
    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content || '';
      if (content) {
        // Send each chunk to the client
        res.write(content);
        fullResponse += content;
        
        // Add a small delay to make streaming more visible
        await new Promise(resolve => setTimeout(resolve, 20));
      }
    }
    
    // End the response
    res.end();
  } catch (error) {
    console.error("OpenAI API error:", error);
    res.write("Sorry, an error occurred while processing your request.");
    res.end();
  }
}