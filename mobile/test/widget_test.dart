import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:route_optimizer/main.dart';
import 'package:route_optimizer/providers/app_providers.dart';

void main() {
  testWidgets('App loads home screen', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiOnlineProvider.overrideWith((ref) async => true),
        ],
        child: const RouteOptimizerApp(),
      ),
    );
    await tester.pump();

    expect(find.text('Route Optimizer'), findsOneWidget);
    expect(find.text('Optimize route'), findsOneWidget);
  });
}
