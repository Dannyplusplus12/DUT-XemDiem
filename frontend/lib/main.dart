import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

const backendBaseUrl = String.fromEnvironment(
  'BACKEND_URL',
  defaultValue: 'http://localhost:8000',
);

void main() {
  runApp(const ContestPortalApp());
}

class ContestPortalApp extends StatelessWidget {
  const ContestPortalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Cổng tra cứu kết quả thi',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0B5ED7)),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final screens = [const PersonalLookupScreen(), const LeaderboardScreen()];

    return Scaffold(
      appBar: AppBar(title: const Text('Cổng tra cứu kết quả thi')),
      body: screens[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Cá nhân'),
          NavigationDestination(icon: Icon(Icons.leaderboard), label: 'Bảng xếp hạng'),
        ],
      ),
    );
  }
}

class PersonalLookupScreen extends StatefulWidget {
  const PersonalLookupScreen({super.key});

  @override
  State<PersonalLookupScreen> createState() => _PersonalLookupScreenState();
}

class _PersonalLookupScreenState extends State<PersonalLookupScreen> {
  final _contestController = TextEditingController();
  final _studentController = TextEditingController();

  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _error;

  Future<void> _lookup() async {
    final contestId = _contestController.text.trim();
    final studentId = _studentController.text.trim();
    if (contestId.isEmpty || studentId.isEmpty) {
      setState(() => _error = 'Vui lòng nhập đầy đủ mã kỳ thi và mã định danh.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final uri = Uri.parse('$backendBaseUrl/contests/$contestId/results/$studentId');
      final response = await http.get(uri);
      if (response.statusCode >= 400) {
        throw Exception('Không tìm thấy dữ liệu phù hợp');
      }

      setState(() {
        _result = jsonDecode(response.body) as Map<String, dynamic>;
      });
    } catch (err) {
      setState(() {
        _error = 'Không thể tra cứu: ${err.toString()}';
        _result = null;
      });
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: ListView(
        children: [
          TextField(
            controller: _contestController,
            decoration: const InputDecoration(labelText: 'Mã kỳ thi'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _studentController,
            decoration: const InputDecoration(labelText: 'Mã định danh (SBD/MSSV)'),
          ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _loading ? null : _lookup,
            child: _loading ? const CircularProgressIndicator() : const Text('Tra cứu'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_result != null) ...[
            const SizedBox(height: 16),
            ResultCard(result: _result!),
          ],
        ],
      ),
    );
  }
}

class ResultCard extends StatelessWidget {
  const ResultCard({super.key, required this.result});

  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final scores = result['component_scores'] as Map<String, dynamic>;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              result['full_name'] ?? '',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            Text('Mã định danh: ${result['student_id']}'),
            Text('Lớp: ${result['class_name']}'),
            const SizedBox(height: 12),
            Text('Tổng điểm', style: Theme.of(context).textTheme.titleMedium),
            Text('${result['total_score']}', style: Theme.of(context).textTheme.displaySmall),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                _MetricTile(label: 'Thứ hạng toàn cuộc', value: '${result['global_rank']}'),
                _MetricTile(label: 'Thứ hạng theo lớp', value: '${result['class_rank']}'),
                _MetricTile(label: 'Tỉ lệ bách phân', value: '${result['percentile']}%'),
              ],
            ),
            const SizedBox(height: 12),
            Text('Điểm trung bình hệ thống: ${result['benchmark_score']}'),
            Text('Chênh lệch so với trung bình: ${result['gap_from_average']}'),
            const SizedBox(height: 12),
            Text('Điểm thành phần', style: Theme.of(context).textTheme.titleMedium),
            ...scores.entries.map((e) => Text('${e.key}: ${e.value}')),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              children: [
                FilledButton.tonal(onPressed: () {}, child: const Text('Vị trí của tôi')),
                OutlinedButton(onPressed: () {}, child: const Text('Trích xuất báo cáo')),
                OutlinedButton(onPressed: () {}, child: const Text('Chia sẻ kết quả')),
              ],
            )
          ],
        ),
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  const _MetricTile({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      width: 220,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.black12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 8),
          Text(value, style: Theme.of(context).textTheme.titleLarge),
        ],
      ),
    );
  }
}

class LeaderboardScreen extends StatefulWidget {
  const LeaderboardScreen({super.key});

  @override
  State<LeaderboardScreen> createState() => _LeaderboardScreenState();
}

class _LeaderboardScreenState extends State<LeaderboardScreen> {
  final _contestController = TextEditingController();
  final _classController = TextEditingController();
  final _highlightController = TextEditingController();

  List<dynamic> _items = [];
  bool _loading = false;
  String? _error;

  Future<void> _loadLeaderboard() async {
    final contestId = _contestController.text.trim();
    if (contestId.isEmpty) {
      setState(() => _error = 'Vui lòng nhập mã kỳ thi.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    final query = <String, String>{'page_size': '100'};
    if (_classController.text.trim().isNotEmpty) {
      query['class_name'] = _classController.text.trim();
    }

    final uri = Uri.parse('$backendBaseUrl/contests/$contestId/leaderboard').replace(queryParameters: query);
    try {
      final response = await http.get(uri);
      if (response.statusCode >= 400) {
        throw Exception('Không thể tải bảng xếp hạng');
      }
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      setState(() {
        _items = body['items'] as List<dynamic>;
      });
    } catch (err) {
      setState(() {
        _error = err.toString();
        _items = [];
      });
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final highlightId = _highlightController.text.trim();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              SizedBox(
                width: 220,
                child: TextField(
                  controller: _contestController,
                  decoration: const InputDecoration(labelText: 'Mã kỳ thi'),
                ),
              ),
              SizedBox(
                width: 220,
                child: TextField(
                  controller: _classController,
                  decoration: const InputDecoration(labelText: 'Thứ hạng theo lớp'),
                ),
              ),
              SizedBox(
                width: 220,
                child: TextField(
                  controller: _highlightController,
                  decoration: const InputDecoration(labelText: 'Mã định danh của tôi'),
                ),
              ),
              FilledButton(
                onPressed: _loading ? null : _loadLeaderboard,
                child: _loading
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator())
                    : const Text('Tải bảng xếp hạng'),
              ),
              OutlinedButton(onPressed: _loadLeaderboard, child: const Text('Vị trí của tôi')),
            ],
          ),
          const SizedBox(height: 12),
          if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
          const SizedBox(height: 12),
          Expanded(
            child: ListView.builder(
              itemCount: _items.length,
              itemBuilder: (context, index) {
                final row = _items[index] as Map<String, dynamic>;
                final isMe = highlightId.isNotEmpty && row['student_id'] == highlightId;
                return Card(
                  color: isMe ? Colors.amber.shade100 : null,
                  child: ListTile(
                    leading: Text('#${row['global_rank']}'),
                    title: Text('${row['full_name']} (${row['student_id']})'),
                    subtitle: Text('Lớp ${row['class_name']} • Tổng điểm ${row['total_score']}'),
                    trailing: Text('${row['percentile']}%'),
                  ),
                );
              },
            ),
          )
        ],
      ),
    );
  }
}
