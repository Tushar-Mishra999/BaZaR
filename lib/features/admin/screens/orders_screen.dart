import 'package:amazon_clone/common/widgets/loader.dart';
import 'package:amazon_clone/features/account/widgets/single_product.dart';
import 'package:amazon_clone/features/admin/services/admin_services.dart';
import 'package:amazon_clone/features/order_details/order_details_screen.dart';
import 'package:amazon_clone/features/admin/widgets/top_buttons_admin.dart';
import 'package:amazon_clone/models/order.dart';
import 'package:flutter/material.dart';

class OrdersScreen extends StatefulWidget {
  OrdersScreen({Key? key}) : super(key: key);
 bool isMount = true;
  @override
  State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> {
  List<Order>? orders;
  final AdminServices adminServices = AdminServices();

  @override
  void initState() {
     widget.isMount = true;
    super.initState();
    fetchOrders();
  }
  
  @override
  void dispose() {
    widget.isMount = false;
    super.dispose();
  }

  void fetchOrders() async {
    orders = await adminServices.fetchAllOrders(context);
    if (widget.isMount) {
      setState(() {});
    }
  }

  @override
  Widget build(BuildContext context) {
    Size size = MediaQuery.of(context).size;
    return orders == null
        ? const Loader()
        : Column(
            children: [
              SizedBox(
                height: size.height * 0.01,
              ),
              TopAdminButtons(),
              SizedBox(
                height: size.height * 0.03,
              ),
              const Text(
                "Orders Placed",
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w500),
              ),
              SizedBox(
                height: size.height * 0.03,
              ),
              Expanded(
                child: GridView.builder(
                  shrinkWrap: true,
                  itemCount: orders!.length,
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2),
                  itemBuilder: (context, index) {
                    final orderData = orders![index];
                    return GestureDetector(
                      onTap: () {
                        Navigator.pushNamed(
                          context,
                          OrderDetailScreen.routeName,
                          arguments: orderData,
                        );
                      },
                      child: SizedBox(
                        height: 140,
                        child: SingleProduct(
                          image: orderData.images[0],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          );
  }
}
