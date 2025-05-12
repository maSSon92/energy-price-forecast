from app.models.compare_predictions import compare_predictions_to_actuals
from app.models.generate_chart import generate_error_chart
from app.models.database import save_prediction, update_actual_price

if __name__ == "__main__":
    print("🚀 Zadanie automatyczne wystartowało...")
    compare_predictions_to_actuals()
    generate_error_chart()
    print("✅ Zadanie zakończone.")
