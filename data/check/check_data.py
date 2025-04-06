from data.check.check_goldth import check_goldth
from data.check.check_goldusd import check_goldusd
from data.check.check_usdthb import check_usdthb
from django.http import JsonResponse
from rest_framework.decorators import api_view

@api_view(['GET'])
def check_data(request):
    try:
        select = request.GET.get('select', '').upper()
        action = request.GET.get('action', 'do').lower()  # Default to 'do' if not specified
        
        # Validate action parameter
        if action not in ['show', 'do']:
            return JsonResponse({
                "status": "error",
                "message": "Invalid action parameter. Use 'show' or 'do'."
            })
            
        # If no select parameter is provided, check all data types
        if not select:
            usdthb_result = check_usdthb(action)
            goldth_result = check_goldth(action)
            goldus_result = check_goldusd(action)
            
            result = {
                "status": "success",
                "message": f"All data types checked successfully. Action: {action}",
                "results": {
                    "USDTHB": usdthb_result,
                    "GOLDTH": goldth_result,
                    "GOLDUS": goldus_result
                }
            }
            return JsonResponse(result)
        
        # Check specific data type based on select parameter
        if select == 'USDTHB':
            result = check_usdthb(action)
        elif select == 'GOLDTH':
            result = check_goldth(action)
        elif select == 'GOLDUS':
            result = check_goldusd(action)
        else:
            result = {"status": "error", "message": "Data type not found"}
            
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    