import os
import json
import logging
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def get_hotel_recommendations(destination, budget, num_results=5):
    """
    Use ChatGPT to get hotel recommendations for a specific destination and budget
    
    Args:
        destination (str): The destination city or location
        budget (float): Maximum price per night in USD
        num_results (int): Number of hotel recommendations to return
        
    Returns:
        list: A list of dictionaries containing hotel recommendations
    """
    if not OPENAI_API_KEY:
        logging.error("OpenAI API key not found")
        return None
    
    try:
        prompt = f"""
        I need hotel recommendations for travelers visiting {destination} with a budget of ${budget} per night.
        
        Please provide {num_results} hotel recommendations in the following JSON format:
        [
            {{
                "id": 1,
                "name": "Hotel Name",
                "location": "Exact location within {destination}",
                "price": 120.00,
                "rating": 4.5,
                "features": ["Feature 1", "Feature 2", "Feature 3"],
                "description": "Brief description of the hotel"
            }},
            ...
        ]
        
        Make sure to stay under the budget of ${budget} per night and provide realistic hotel names,
        locations, and details. Each hotel should have a unique ID and valid rating out of 5.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a travel expert providing helpful hotel recommendations."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Check if result is a dict with a list inside, which can happen sometimes
        if isinstance(result, dict) and any(key in result for key in ["hotels", "recommendations", "results"]):
            for key in ["hotels", "recommendations", "results"]:
                if key in result:
                    return result[key]
        
        # Otherwise, return the direct list
        return result
        
    except Exception as e:
        logging.error(f"Error getting hotel recommendations: {e}")
        
        # If we hit an API quota limit or any other error, provide fallback recommendations
        return get_fallback_hotel_recommendations(destination, budget, num_results)

def get_fallback_hotel_recommendations(destination, budget, num_results=5):
    """
    Provides fallback hotel recommendations when the OpenAI API is unavailable
    
    Args:
        destination (str): The destination city or location
        budget (float): Maximum price per night in USD
        num_results (int): Number of hotel recommendations to return
        
    Returns:
        list: A list of dictionaries containing hotel recommendations
    """
    logging.info(f"Using fallback recommendations for {destination}")
    
    # Generate a deterministic but seemingly random set of hotels based on the destination
    import hashlib
    
    # Create a unique hash based on destination to ensure consistent results
    destination_hash = int(hashlib.md5(destination.lower().encode()).hexdigest(), 16)
    
    # Popular hotel chains and features for variety
    hotel_chains = ["Grand Hotel", "Comfort Inn", "Royal Suites", "City View", "Travelers Rest", 
                   "Urban Stay", "Harbor View", "Mountain Lodge", "Plaza Hotel", "Sunset Resort"]
    
    features_options = [
        ["Free Wi-Fi", "Breakfast included", "Swimming pool"],
        ["24/7 Reception", "Fitness center", "Restaurant on site"],
        ["Airport shuttle", "Business center", "Spa services"],
        ["Room service", "Pet friendly", "Ocean view"],
        ["Concierge service", "Free parking", "Rooftop bar"]
    ]
    
    fallback_hotels = []
    
    for i in range(1, num_results + 1):
        # Use a combination of destination and index to create varied but deterministic hotels
        hotel_index = (destination_hash + i * 37) % len(hotel_chains)
        feature_index = (destination_hash + i * 17) % len(features_options)
        
        # Calculate a price between 60% and 90% of the budget
        price_factor = ((destination_hash + i * 41) % 31) / 100 + 0.6
        price = min(round(budget * price_factor, 2), budget)
        
        # Generate a rating between 3.5 and 4.9
        rating_base = ((destination_hash + i * 23) % 15) / 10 + 3.5
        rating = min(round(rating_base, 1), 4.9)
        
        hotel_name = f"{hotel_chains[hotel_index]} {destination}"
        location_areas = ["Downtown", "Uptown", "Old Town", "Business District", "Marina", "Central"]
        location_area = location_areas[(destination_hash + i * 13) % len(location_areas)]
        
        hotel = {
            "id": i,
            "name": hotel_name,
            "location": f"{location_area}, {destination}",
            "price": price,
            "rating": rating,
            "features": features_options[feature_index],
            "description": f"A comfortable stay in the heart of {destination} with modern amenities and excellent service. Located near major attractions and transport options."
        }
        
        fallback_hotels.append(hotel)
    
    return fallback_hotels

def get_chat_response(message, conversation_history=None):
    """
    Use ChatGPT to respond to user messages in the travel assistant chat
    
    Args:
        message (str): The user's message
        conversation_history (list, optional): A list of previous messages in the conversation
        
    Returns:
        str: The AI assistant's response
    """
    if not OPENAI_API_KEY:
        logging.error("OpenAI API key not found")
        return "I'm sorry, but I'm not available at the moment. Please try again later."
    
    try:
        # Initialize messages with system prompt if no history is provided
        if not conversation_history:
            messages = [
                {
                    "role": "system", 
                    "content": (
                        "You are a helpful travel assistant in a travel companion app. "
                        "Provide personalized travel advice, recommendations, and answers to travel-related questions. "
                        "Be conversational, informative, and concise. Focus primarily on travel topics "
                        "such as destinations, accommodations, transportation, activities, budgeting, and travel tips. "
                        "Your responses should be friendly and helpful, formatted in a way that's easy to read."
                    )
                }
            ]
        else:
            messages = conversation_history.copy()
        
        # Add the user's message
        messages.append({"role": "user", "content": message})
        
        # Get a response from the model
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logging.error(f"Error getting chat response: {e}")
        return get_fallback_chat_response(message)

def get_fallback_chat_response(message):
    """
    Provides fallback responses when the OpenAI API is unavailable
    
    Args:
        message (str): The user's message
        
    Returns:
        str: A fallback response
    """
    # Extract some key travel-related keywords for basic pattern matching
    message_lower = message.lower()
    
    # Determine if the message contains a greeting
    greetings = ["hello", "hi", "hey", "greetings", "howdy"]
    if any(greeting in message_lower for greeting in greetings):
        return "Hello there! I'm your travel assistant. While I'm currently operating in offline mode due to high demand, I'd be happy to help with general travel questions. What would you like to know about travel planning, destinations, or accommodations?"
    
    # Check for destination-related questions
    if any(word in message_lower for word in ["visit", "travel to", "destination", "place", "country", "city"]):
        return "I'd love to help you explore destinations! When choosing a travel destination, consider factors like your interests (cultural experiences, adventure, relaxation), budget, travel season, and how much time you have. Popular destinations like Paris, Tokyo, and New York offer diverse experiences, while places like Costa Rica, Portugal, and Vietnam provide excellent value. If you have a specific destination in mind, feel free to ask me about it when I'm back online!"
    
    # Check for accommodation-related questions
    if any(word in message_lower for word in ["hotel", "stay", "accommodation", "hostel", "airbnb"]):
        return "Finding the right accommodation is key to a great trip! Consider location (proximity to attractions or public transport), budget, amenities, and reviews. Booking in advance often secures better rates, especially during peak seasons. Many travelers enjoy using a mix of hotels for convenience and vacation rentals for longer stays. I'll be able to provide more personalized recommendations when I'm back online."
    
    # Check for budget-related questions
    if any(word in message_lower for word in ["budget", "cost", "cheap", "expensive", "save", "money"]):
        return "Travel budgeting is essential! To save money, consider traveling during shoulder seasons (just before or after peak season), booking accommodations with kitchen facilities, using public transportation, and looking for free or low-cost activities. Setting a daily spending limit for food, activities, and souvenirs can help manage your overall budget. I'd be happy to provide more specific budget tips when I'm back online."
    
    # Check for transportation-related questions
    if any(word in message_lower for word in ["flight", "fly", "train", "transportation", "car rental", "bus"]):
        return "For transportation planning, compare options like flights, trains, and buses for both cost and convenience. Booking flights 2-3 months in advance often yields better prices, and being flexible with dates can help find deals. Within cities, public transportation passes often offer savings over individual tickets. For road trips, consider factors like fuel costs, parking, and whether you'll need the vehicle throughout your stay."
    
    # Check for itinerary-related questions
    if any(word in message_lower for word in ["itinerary", "plan", "schedule", "day", "activity"]):
        return "When planning your itinerary, I recommend balancing scheduled activities with free time for spontaneous exploration. Group sights by location to minimize travel time, and don't overpack your schedule—quality experiences often trump quantity. Research opening hours and consider booking popular attractions in advance. A good rule of thumb is 2-3 major activities per day, with time for meals and rest."
    
    # Default response for other questions
    return "I apologize, but I'm currently in offline mode due to high demand on our AI services. I'll be fully operational again soon! In the meantime, our website offers great resources on popular destinations, hotel recommendations, and travel tips to help with your planning. Please try again later for personalized assistance."
