from django.urls import path
from . import views

app_name = "cars"

urlpatterns = [
    # Home
    path("", views.HomeView, name="home"),

    # Static pages
    path("find-new/", views.find_new, name="find_new"),

    # Cars
    path("cars/", views.CarsListView, name="all_cars"),
    path("cars/all_cars/", views.CarsListView, name="all_cars_alias"),
    path("cars/used-cars/", views.UsedCarsListView, name="used_cars"),
    path("cars/inventory/", views.InventoryListView, name="inventory"),
    path("cars/inventory/import-static/", views.ImportStaticCarsView, name="import_static_cars"),
    path("cars/upcoming-cars/", views.UpcomingCarsListView, name="upcoming_cars"),
    path("cars/electric-cars/", views.ElectricCarsListView, name="electric_cars"),
    path("cars/new-cars/", views.NewCarsListView, name="new_cars"),
    path("cars/<str:vin>/", views.CarDetailView, name="car_detail"),
    path("add/", views.CarCreateView, name="add"),
    path("cars/<str:vin>/edit/", views.CarUpdateView, name="car_edit"),
    path("cars/<str:vin>/delete/", views.CarDeleteView, name="car_delete"),
    path("cars/<str:vin>/price/", views.QuickPriceUpdateView, name="car_price_update"),
    path("cars/<str:vin>/stock/", views.QuickStockUpdateView, name="car_stock_update"),
    path("category/<str:category_name>/", views.CarCategoryView, name="car_category"),
    
    # Compare
    path("compare/", views.compare_cars, name="compare_cars"),
    path("compare/add/<int:car_id>/", views.add_to_compare, name="add_to_compare"),
    path("compare/remove/<int:car_id>/", views.remove_from_compare, name="remove_from_compare"),

    # Test drives
    path("testdrives/", views.TestDrivesView, name="test_drives"),
    path("testdrives/schedule/<str:vin>/", views.ScheduleTestDriveView, name="schedule_test_drive"),
    path("testdrives/update/<uuid:drive_id>/<str:status>/", views.UpdateTestDriveStatusView, name="update_test_drive_status"),
    
    # Messaging
    path("inbox/", views.InboxView, name="inbox"),
    path("chat/<str:other_user_id>/", views.ChatView, name="chat"),
    
    # Deals
    path("deals/propose/<uuid:listing_id>/", views.ProposeDealView, name="propose_deal"),
    path("deals/update/<uuid:deal_id>/<str:status>/", views.UpdateDealStatusView, name="update_deal_status"),
    path("listing/withdraw/<uuid:listing_id>/", views.WithdrawListingView, name="withdraw_listing"),

    # Purchase
    path("purchase/<str:vin>/", views.PurchaseCarView, name="purchase_car"),
    path("purchase/razorpay/callback/", views.RazorpayCallbackView, name="razorpay_callback"),
    path("purchase/success/<uuid:purchase_id>/", views.PurchaseSuccessView, name="purchase_success"),
    path("purchase/receipt/<uuid:purchase_id>/", views.DownloadReceiptView, name="download_receipt"),

    # Wishlist
    path("wishlist/", views.wishlist_page, name="wishlist"),
    path("wishlist/toggle/<int:car_id>/", views.toggle_wishlist, name="toggle_wishlist"),
]
