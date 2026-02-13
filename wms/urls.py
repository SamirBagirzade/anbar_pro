from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from wms.masters.api import VendorViewSet, WarehouseViewSet, OutgoingLocationViewSet, ItemViewSet
from wms.purchasing.api import PurchaseViewSet
from wms.issuing.api import IssueViewSet
from wms.inventory.api import (
    StockBalanceViewSet,
    StockMovementViewSet,
    TransferViewSet,
    AdjustmentViewSet,
)
from wms.inventory import views as inventory_views
from wms.masters import views as masters_views
from wms.purchasing import views as purchasing_views
from wms.issuing import views as issuing_views

router = DefaultRouter()
router.register(r"vendors", VendorViewSet)
router.register(r"warehouses", WarehouseViewSet)
router.register(r"outgoing-locations", OutgoingLocationViewSet)
router.register(r"items", ItemViewSet)
router.register(r"purchases", PurchaseViewSet)
router.register(r"issues", IssueViewSet)
router.register(r"transfers", TransferViewSet)
router.register(r"adjustments", AdjustmentViewSet)
router.register(r"stock-balances", StockBalanceViewSet)
router.register(r"stock-movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/", include(router.urls)),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", inventory_views.warehouse_stock, name="warehouse_stock"),
    path("inventory/movements/", inventory_views.recent_movements, name="recent_movements"),
    path("inventory/items/<int:item_id>/", inventory_views.item_detail, name="item_detail"),
    path("masters/vendors/", masters_views.vendor_list, name="vendor_list"),
    path("masters/vendors/new/", masters_views.vendor_create, name="vendor_create"),
    path("masters/vendors/<int:vendor_id>/edit/", masters_views.vendor_edit, name="vendor_edit"),
    path("masters/vendors/<int:vendor_id>/delete/", masters_views.vendor_delete, name="vendor_delete"),
    path("masters/vendors/search/", masters_views.vendor_search, name="vendor_search"),
    path("masters/warehouses/", masters_views.warehouse_list, name="warehouse_list"),
    path("masters/warehouses/new/", masters_views.warehouse_create, name="warehouse_create"),
    path("masters/warehouses/<int:warehouse_id>/edit/", masters_views.warehouse_edit, name="warehouse_edit"),
    path("masters/warehouses/<int:warehouse_id>/delete/", masters_views.warehouse_delete, name="warehouse_delete"),
    path("masters/outgoing-locations/", masters_views.outgoing_location_list, name="outgoing_location_list"),
    path("masters/outgoing-locations/new/", masters_views.outgoing_location_create, name="outgoing_location_create"),
    path("masters/outgoing-locations/<int:location_id>/edit/", masters_views.outgoing_location_edit, name="outgoing_location_edit"),
    path("masters/outgoing-locations/<int:location_id>/delete/", masters_views.outgoing_location_delete, name="outgoing_location_delete"),
    path("masters/units/", masters_views.unit_list, name="unit_list"),
    path("masters/units/new/", masters_views.unit_create, name="unit_create"),
    path("masters/units/<int:unit_id>/edit/", masters_views.unit_edit, name="unit_edit"),
    path("masters/units/<int:unit_id>/delete/", masters_views.unit_delete, name="unit_delete"),
    path("masters/units/search/", masters_views.unit_search, name="unit_search"),
    path("masters/items/", masters_views.item_list, name="item_list"),
    path("masters/items/search/", masters_views.item_search, name="item_search"),
    path("masters/items/new/", masters_views.item_create, name="item_create"),
    path("masters/items/<int:item_id>/edit/", masters_views.item_edit, name="item_edit"),
    path("masters/items/<int:item_id>/delete/", masters_views.item_delete, name="item_delete"),
    path("purchasing/purchases/", purchasing_views.purchase_list, name="purchase_list"),
    path("purchasing/purchases/new/", purchasing_views.purchase_create, name="purchase_create"),
    path("purchasing/purchases/<int:purchase_id>/edit/", purchasing_views.purchase_edit, name="purchase_edit"),
    path("purchasing/purchases/<int:purchase_id>/", purchasing_views.purchase_detail, name="purchase_detail"),
    path("issuing/issues/", issuing_views.issue_list, name="issue_list"),
    path("issuing/issues/new/", issuing_views.issue_create, name="issue_create"),
    path("issuing/issues/<int:issue_id>/", issuing_views.issue_detail, name="issue_detail"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
