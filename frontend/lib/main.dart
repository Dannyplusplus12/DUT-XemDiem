import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

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
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1C4B82)),
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
      appBar: AppBar(
        title: const Text('Cổng tra cứu kết quả thi'),
      ),
      body: screens[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (v) => setState(() => _index = v),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.person_search), label: 'Cá nhân'),
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
  String? _error;
  bool _loading = false;

  Future<void> _lookup() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final contestId = _contestController.text.trim();
      final studentId = _studentController.text.trim();

      final uri = Uri.parse('http://localhost:8000/results/$contestId/$studentId');
      final res = await http.get(uri);
      if (res.statusCode >= 400) {
        throw Exception('Không tìm thấy dữ liệu phù hợp');
      }

      setState(() {
        _result = jsonDecode(res.body) as Map<String, dynamic>;
      });
    } catch (_) {
      setState(() {
        _error = 'Không thể tải kết quả. Vui lòng kiểm tra mã kỳ thi và mã định danh.';
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
            decoration: const InputDecoration(labelText: 'Mã định danh (MSSV/SBD)'),
          ),
          const SizedBox(height: 12),
          FilledButton(
            onPressed: _loading ? null : _lookup,
            child: const Text('Tra cứu'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_result != null) ...[
            const SizedBox(height: 20),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Tổng điểm: ${_result!["total_score"]}', style: Theme.of(context).textTheme.headlineSmall),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        _MetricCard(label: 'Thứ hạng toàn cuộc', value: '${_result!["global_rank"]}'),
                        _MetricCard(label: 'Thứ hạng trong lớp', value: '${_result!["class_rank"]}'),
                        _MetricCard(label: 'Tỉ lệ bách phân', value: '${_result!["percentile"]}%'),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text('Điểm trung bình toàn cuộc: ${_result!["benchmark_score"]}'),
                    Text('Chênh lệch: ${_result!["score_difference_from_benchmark"]}'),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      children: [
                        OutlinedButton(onPressed: () {}, child: const Text('Chia sẻ kết quả')),
                        OutlinedButton(onPressed: () {}, child: const Text('Trích xuất báo cáo')),
                      ],
                    )
                  ],
                ),
              ),
            )
          ]
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 220,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.8),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.black12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label),
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
  final _myIdController = TextEditingController();

  List<dynamic> _rows = [];
  String _sortBy = 'global_rank';
  String _order = 'asc';

  Future<void> _load() async {
    final contestId = _contestController.text.trim();
    if (contestId.isEmpty) return;

    final params = <String, String>{'sort_by': _sortBy, 'order': _order, 'page_size': '100'};
    if (_classController.text.trim().isNotEmpty) {
      params['class_name'] = _classController.text.trim();
    }

    final uri = Uri.parse('http://localhost:8000/leaderboard/$contestId').replace(queryParameters: params);
    final res = await http.get(uri);
    if (res.statusCode < 400) {
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      setState(() {
        _rows = body['items'] as List<dynamic>;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final myId = _myIdController.text.trim();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
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
                  controller: _myIdController,
                  decoration: const InputDecoration(labelText: 'Mã định danh của tôi'),
                ),
              ),
              FilledButton(onPressed: _load, child: const Text('Tải bảng xếp hạng')),
              OutlinedButton(onPressed: _load, child: const Text('Vị trí của tôi')),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              itemCount: _rows.length,
              itemBuilder: (context, index) {
                final row = _rows[index] as Map<String, dynamic>;
                final isMe = myId.isNotEmpty && row['student_id']?.toString() == myId;
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
