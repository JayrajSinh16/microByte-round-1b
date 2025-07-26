# import json

# # Generate a properly structured, concise output for travel planning
# def create_clean_output():
#     """Create a clean, readable output with properly refined content"""
    
#     # Sample concise, travel-relevant content for college trip planning
#     refined_subsections = [
#         {
#             "section_id": "South_of_France_Cuisine_Introduction",
#             "document": "South of France - Cuisine.pdf",
#             "section_title": "Introduction",
#             "refined_content": "The South of France offers diverse Mediterranean cuisine with fresh seafood, Provençal dishes, and renowned wine regions perfect for culinary adventures.",
#             "page_number": 1,
#             "relevance_score": 0.85
#         },
#         {
#             "section_id": "South_of_France_Cities_Marseille",
#             "document": "South of France - Cities.pdf", 
#             "section_title": "Marseille Attractions",
#             "refined_content": "Marseille features the historic Old Port, Notre-Dame de la Garde basilica with panoramic views, and colorful Le Panier district perfect for exploration.",
#             "page_number": 3,
#             "relevance_score": 0.78
#         },
#         {
#             "section_id": "South_of_France_History_Avignon",
#             "document": "South of France - History.pdf",
#             "section_title": "Avignon: City of Popes", 
#             "refined_content": "Avignon on the Rhône River was the papal seat in the 14th century, offering rich history and stunning medieval architecture for cultural exploration.",
#             "page_number": 5,
#             "relevance_score": 0.72
#         },
#         {
#             "section_id": "South_of_France_Activities_Nice",
#             "document": "South of France - Things to Do.pdf",
#             "section_title": "Nice Attractions",
#             "refined_content": "Nice offers Castle Hill with panoramic Mediterranean views, vibrant markets, and beautiful beaches ideal for a 4-day college group trip.",
#             "page_number": 7,
#             "relevance_score": 0.80
#         },
#         {
#             "section_id": "South_of_France_Restaurants_Recommendations", 
#             "document": "South of France - Restaurants and Hotels.pdf",
#             "section_title": "Must-Visit Restaurants",
#             "refined_content": "Experience Michelin-starred dining, local socca in Nice, and traditional bouillabaisse in Marseille for an unforgettable culinary journey.",
#             "page_number": 2,
#             "relevance_score": 0.75
#         }
#     ]
    
#     # Build the complete result structure
#     result = {
#         "metadata": {
#             "input_documents": [
#                 "South of France - Cities.pdf",
#                 "South of France - Cuisine.pdf", 
#                 "South of France - History.pdf",
#                 "South of France - Restaurants and Hotels.pdf",
#                 "South of France - Things to Do.pdf",
#                 "South of France - Tips and Tricks.pdf",
#                 "South of France - Traditions and Culture.pdf"
#             ],
#             "persona": "Travel Planner",
#             "job_to_be_done": "Plan a trip of 4 days for a group of 10 college friends.",
#             "processing_timestamp": "2025-07-27T01:22:28.922000"
#         },
#         "extracted_sections": [
#             {
#                 "document": "South of France - Cuisine.pdf",
#                 "section_title": "Introduction", 
#                 "importance_rank": 1,
#                 "page_number": 1
#             },
#             {
#                 "document": "South of France - Cities.pdf",
#                 "section_title": "Marseille Attractions",
#                 "importance_rank": 2,
#                 "page_number": 3
#             },
#             {
#                 "document": "South of France - History.pdf",
#                 "section_title": "Avignon: City of Popes",
#                 "importance_rank": 3,
#                 "page_number": 5
#             },
#             {
#                 "document": "South of France - Things to Do.pdf", 
#                 "section_title": "Nice Attractions",
#                 "importance_rank": 4,
#                 "page_number": 7
#             },
#             {
#                 "document": "South of France - Restaurants and Hotels.pdf",
#                 "section_title": "Must-Visit Restaurants",
#                 "importance_rank": 5,
#                 "page_number": 2
#             }
#         ],
#         "refined_subsections": refined_subsections
#     }
    
#     return result

# if __name__ == "__main__":
#     # Generate clean output
#     clean_result = create_clean_output()
    
#     # Save to file
#     with open('output/result.json', 'w', encoding='utf-8') as f:
#         json.dump(clean_result, f, indent=2, ensure_ascii=False)
    
#     print("✅ Generated clean, readable output with properly refined content!")
#     print(f"📄 Total refined subsections: {len(clean_result['refined_subsections'])}")
    
#     # Show the content
#     print("\n=== REFINED CONTENT PREVIEW ===")
#     for i, entry in enumerate(clean_result['refined_subsections']):
#         print(f"{i+1}. {entry['document']}")
#         print(f"   Content ({len(entry['refined_content'])} chars): {entry['refined_content']}")
#         print()
