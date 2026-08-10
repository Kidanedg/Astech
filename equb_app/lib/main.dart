import 'package:flutter/material.dart';

void main() {
  runApp(const EqubApp());
}

// ============================================================
// IDFS EQUb MOBILE PROTOTYPE
// Indigenous Digital Financial System
// Ethiopian Rotating Savings & Credit Platform
// ============================================================

class EqubApp extends StatelessWidget {
  const EqubApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IDFS Equb',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0B5CAD),
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: const Color(0xFFF5F7FA),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0B5CAD),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          elevation: 1,
          margin: const EdgeInsets.symmetric(vertical: 6),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      home: const MainNavigation(),
    );
  }
}

// ============================================================
// DATA MODELS
// ============================================================

class EqubMember {
  final String name;
  final String phone;
  final double contribution;
  final double totalContribution;
  final int rounds;
  final bool active;

  const EqubMember({
    required this.name,
    required this.phone,
    required this.contribution,
    required this.totalContribution,
    required this.rounds,
    this.active = true,
  });

  double probability(double total) {
    if (total <= 0) return 0;
    return contribution / total;
  }
}

class EqubTransaction {
  final String title;
  final String date;
  final double amount;
  final String type;
  final bool incoming;

  const EqubTransaction({
    required this.title,
    required this.date,
    required this.amount,
    required this.type,
    required this.incoming,
  });
}

// ============================================================
// SAMPLE DATA
// ============================================================

final List<EqubMember> members = [
  const EqubMember(
    name: 'Kidane Desta',
    phone: '09XX XXX XXX',
    contribution: 3000,
    totalContribution: 18000,
    rounds: 6,
  ),
  const EqubMember(
    name: 'Mekdes Tesfay',
    phone: '09XX XXX XXX',
    contribution: 2500,
    totalContribution: 15000,
    rounds: 6,
  ),
  const EqubMember(
    name: 'Daniel Gebre',
    phone: '09XX XXX XXX',
    contribution: 2000,
    totalContribution: 12000,
    rounds: 6,
  ),
  const EqubMember(
    name: 'Hana Abraha',
    phone: '09XX XXX XXX',
    contribution: 1500,
    totalContribution: 9000,
    rounds: 6,
  ),
  const EqubMember(
    name: 'Samuel Tesfay',
    phone: '09XX XXX XXX',
    contribution: 1000,
    totalContribution: 6000,
    rounds: 6,
  ),
];

final List<EqubTransaction> transactions = [
  const EqubTransaction(
    title: 'Monthly Contribution',
    date: '10 Aug 2026',
    amount: 3000,
    type: 'Contribution',
    incoming: false,
  ),
  const EqubTransaction(
    title: 'Equb Round Payout',
    date: '01 Aug 2026',
    amount: 15000,
    type: 'Payout',
    incoming: true,
  ),
  const EqubTransaction(
    title: 'Monthly Contribution',
    date: '10 Jul 2026',
    amount: 3000,
    type: 'Contribution',
    incoming: false,
  ),
  const EqubTransaction(
    title: 'Monthly Contribution',
    date: '10 Jun 2026',
    amount: 3000,
    type: 'Contribution',
    incoming: false,
  ),
];

// ============================================================
// MAIN NAVIGATION
// ============================================================

class MainNavigation extends StatefulWidget {
  const MainNavigation({super.key});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int currentIndex = 0;

  final List<Widget> pages = const [
    DashboardPage(),
    EqubPage(),
    MembersPage(),
    TransactionsPage(),
    ProfilePage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: pages[currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.account_balance_outlined),
            selectedIcon: Icon(Icons.account_balance),
            label: 'Equb',
          ),
          NavigationDestination(
            icon: Icon(Icons.people_outline),
            selectedIcon: Icon(Icons.people),
            label: 'Members',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long),
            label: 'Transactions',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}

// ============================================================
// DASHBOARD
// ============================================================

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});

  double get totalFund {
    return members.fold(0, (sum, m) => sum + m.contribution);
  }

  double get totalContributed {
    return members.fold(0, (sum, m) => sum + m.totalContribution);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'IDFS Equb',
              style: TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              'Indigenous Digital Financial System',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.normal,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.more_vert),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _welcomeCard(),

            const SizedBox(height: 18),

            const Text(
              'Financial Overview',
              style: TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 10),

            Row(
              children: [
                Expanded(
                  child: _metricCard(
                    context,
                    'Current Round',
                    '15,000 ETB',
                    Icons.account_balance_wallet,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _metricCard(
                    context,
                    'My Contribution',
                    '3,000 ETB',
                    Icons.payments,
                  ),
                ),
              ],
            ),

            Row(
              children: [
                Expanded(
                  child: _metricCard(
                    context,
                    'Total Saved',
                    '${_format(totalContributed)} ETB',
                    Icons.savings,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _metricCard(
                    context,
                    'Members',
                    '${members.length}',
                    Icons.groups,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 18),

            _roundCard(context),

            const SizedBox(height: 18),

            const Text(
              'My Equb Statistics',
              style: TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 10),

            _statisticsCard(),

            const SizedBox(height: 18),

            const Text(
              'Quick Actions',
              style: TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 10),

            Row(
              children: [
                Expanded(
                  child: _actionButton(
                    context,
                    'Contribute',
                    Icons.add_card,
                    () => _showContributionDialog(context),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _actionButton(
                    context,
                    'Members',
                    Icons.people,
                    () {},
                  ),
                ),
              ],
            ),

            const SizedBox(height: 20),

            const Text(
              'Recent Activity',
              style: TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            ...transactions.take(3).map(
                  (transaction) => _transactionTile(transaction),
                ),
          ],
        ),
      ),
    );
  }

  Widget _welcomeCard() {
    return Builder(
      builder: (context) {
        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            gradient: const LinearGradient(
              colors: [
                Color(0xFF0B5CAD),
                Color(0xFF1679D1),
              ],
            ),
          ),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Good afternoon,',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                ),
              ),
              SizedBox(height: 5),
              Text(
                'Kidane Desta',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 12),
              Text(
                'You are an active member of\nAksum Community Equb.',
                style: TextStyle(
                  color: Colors.white,
                  height: 1.4,
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _metricCard(
    BuildContext context,
    String title,
    String value,
    IconData icon,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              icon,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 12),
            Text(
              title,
              style: const TextStyle(
                fontSize: 12,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              value,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _roundCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor:
                      Theme.of(context).colorScheme.primaryContainer,
                  child: Icon(
                    Icons.rotate_right,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Current Equb Round',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        'Round 6 of 12',
                        style: TextStyle(
                          color: Colors.grey,
                        ),
                      ),
                    ],
                  ),
                ),
                const Text(
                  'ACTIVE',
                  style: TextStyle(
                    color: Colors.green,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            LinearProgressIndicator(
              value: 6 / 12,
              minHeight: 8,
              borderRadius: BorderRadius.circular(8),
            ),
            const SizedBox(height: 10),
            const Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('6 rounds completed'),
                Text('6 remaining'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _statisticsCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          children: [
            _statRow(
              'My contribution',
              '3,000 ETB / round',
            ),
            _statRow(
              'Total contribution',
              '18,000 ETB',
            ),
            _statRow(
              'Rounds completed',
              '6',
            ),
            _statRow(
              'Weighted probability',
              '31.6%',
            ),
            _statRow(
              'Contribution rank',
              '#1',
            ),
          ],
        ),
      ),
    );
  }

  Widget _statRow(String title, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Expanded(child: Text(title)),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _actionButton(
    BuildContext context,
    String title,
    IconData icon,
    VoidCallback action,
  ) {
    return FilledButton.icon(
      onPressed: action,
      icon: Icon(icon),
      label: Text(title),
      style: FilledButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 14),
      ),
    );
  }

  Widget _transactionTile(EqubTransaction transaction) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          child: Icon(
            transaction.incoming
                ? Icons.arrow_downward
                : Icons.arrow_upward,
          ),
        ),
        title: Text(transaction.title),
        subtitle: Text(transaction.date),
        trailing: Text(
          '${transaction.incoming ? '+' : '-'}${_format(transaction.amount)} ETB',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: transaction.incoming
                ? Colors.green
                : Colors.redAccent,
          ),
        ),
      ),
    );
  }

  void _showContributionDialog(BuildContext context) {
    final controller = TextEditingController(text: '3000');

    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Make Contribution'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(
            labelText: 'Contribution Amount',
            suffixText: 'ETB',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text(
                    'Contribution recorded successfully.',
                  ),
                ),
              );
            },
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// EQUB PAGE
// ============================================================

class EqubPage extends StatelessWidget {
  const EqubPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Equb'),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.add),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _equbSummary(context),
          const SizedBox(height: 16),
          _sectionTitle('Equb Information'),
          _infoCard(),
          const SizedBox(height: 16),
          _sectionTitle('Contribution Structure'),
          _contributionStructure(),
          const SizedBox(height: 16),
          _sectionTitle('Round Schedule'),
          ...List.generate(
            6,
            (index) => _roundTile(
              context,
              index + 1,
              index < 5 ? 'Completed' : 'Current',
            ),
          ),
        ],
      ),
    );
  }

  Widget _equbSummary(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary,
        borderRadius: BorderRadius.circular(20),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Aksum Community Equb',
            style: TextStyle(
              color: Colors.white,
              fontSize: 21,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Monthly rotating savings group',
            style: TextStyle(
              color: Colors.white70,
            ),
          ),
          SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: _SummaryItem(
                  title: 'Members',
                  value: '5',
                ),
              ),
              Expanded(
                child: _SummaryItem(
                  title: 'Contribution',
                  value: '3,000 ETB',
                ),
              ),
              Expanded(
                child: _SummaryItem(
                  title: 'Round',
                  value: '6/12',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _infoCard() {
    return Card(
      child: Column(
        children: [
          const ListTile(
            leading: Icon(Icons.groups),
            title: Text('Equb Chairperson'),
            trailing: Text('Kidane Desta'),
          ),
          const ListTile(
            leading: Icon(Icons.calendar_month),
            title: Text('Frequency'),
            trailing: Text('Monthly'),
          ),
          const ListTile(
            leading: Icon(Icons.account_balance),
            title: Text('Current Fund'),
            trailing: Text('15,000 ETB'),
          ),
          const ListTile(
            leading: Icon(Icons.event),
            title: Text('Next Draw'),
            trailing: Text('01 Sep 2026'),
          ),
        ],
      ),
    );
  }

  Widget _contributionStructure() {
    return Card(
      child: Column(
        children: [
          const ListTile(
            leading: Icon(Icons.payments),
            title: Text('My Monthly Contribution'),
            trailing: Text(
              '3,000 ETB',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          const ListTile(
            leading: Icon(Icons.calculate),
            title: Text('Expected Round Fund'),
            trailing: Text(
              '15,000 ETB',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          const ListTile(
            leading: Icon(Icons.percent),
            title: Text('Weighted Probability'),
            trailing: Text(
              '31.6%',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _roundTile(
    BuildContext context,
    int round,
    String status,
  ) {
    final current = status == 'Current';

    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: current
              ? Theme.of(context).colorScheme.primary
              : Colors.green.shade100,
          child: Text(
            '$round',
            style: TextStyle(
              color: current ? Colors.white : Colors.green.shade800,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        title: Text('Round $round'),
        subtitle: Text(
          current ? 'Currently active' : 'Completed',
        ),
        trailing: current
            ? const Chip(
                label: Text('CURRENT'),
              )
            : const Icon(
                Icons.check_circle,
                color: Colors.green,
              ),
      ),
    );
  }
}

class _SummaryItem extends StatelessWidget {
  final String title;
  final String value;

  const _SummaryItem({
    required this.title,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 15,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 4),
        Text(
          title,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 11,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

// ============================================================
// MEMBERS PAGE
// ============================================================

class MembersPage extends StatefulWidget {
  const MembersPage({super.key});

  @override
  State<MembersPage> createState() => _MembersPageState();
}

class _MembersPageState extends State<MembersPage> {
  String search = '';

  double get totalContribution {
    return members.fold(
      0,
      (sum, member) => sum + member.contribution,
    );
  }

  @override
  Widget build(BuildContext context) {
    final filtered = members
        .where(
          (m) => m.name.toLowerCase().contains(search.toLowerCase()),
        )
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Equb Members'),
        actions: [
          IconButton(
            onPressed: () => _addMember(context),
            icon: const Icon(Icons.person_add),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              onChanged: (value) {
                setState(() {
                  search = value;
                });
              },
              decoration: InputDecoration(
                hintText: 'Search members...',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
            ),
          ),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const Icon(Icons.groups),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment:
                            CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Total Members',
                            style: TextStyle(color: Colors.grey),
                          ),
                          Text(
                            '${members.length}',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 20,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        const Text(
                          'Round Fund',
                          style: TextStyle(color: Colors.grey),
                        ),
                        Text(
                          '${_format(totalContribution)} ETB',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 8),

          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: filtered.length,
              itemBuilder: (context, index) {
                final member = filtered[index];
                return _memberCard(member);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _memberCard(EqubMember member) {
    final probability = member.probability(totalContribution);

    return Card(
      child: ExpansionTile(
        leading: CircleAvatar(
          child: Text(
            member.name.substring(0, 1),
          ),
        ),
        title: Text(
          member.name,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
        subtitle: Text(member.phone),
        trailing: Text(
          '${(probability * 100).toStringAsFixed(1)}%',
          style: const TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
              16,
              0,
              16,
              16,
            ),
            child: Column(
              children: [
                _memberInfo(
                  'Contribution / Round',
                  '${_format(member.contribution)} ETB',
                ),
                _memberInfo(
                  'Total Contribution',
                  '${_format(member.totalContribution)} ETB',
                ),
                _memberInfo(
                  'Completed Rounds',
                  '${member.rounds}',
                ),
                _memberInfo(
                  'Weighted Probability',
                  '${(probability * 100).toStringAsFixed(2)}%',
                ),
                const SizedBox(height: 8),
                LinearProgressIndicator(
                  value: probability,
                  minHeight: 8,
                  borderRadius: BorderRadius.circular(8),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _memberInfo(String title, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          Expanded(child: Text(title)),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  void _addMember(BuildContext context) {
    final name = TextEditingController();
    final phone = TextEditingController();
    final contribution = TextEditingController();

    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Register Member'),
        content: SingleChildScrollView(
          child: Column(
            children: [
              TextField(
                controller: name,
                decoration: const InputDecoration(
                  labelText: 'Full Name',
                ),
              ),
              TextField(
                controller: phone,
                decoration: const InputDecoration(
                  labelText: 'Phone Number',
                ),
              ),
              TextField(
                controller: contribution,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Monthly Contribution',
                  suffixText: 'ETB',
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Member registration recorded.'),
                ),
              );
            },
            child: const Text('Register'),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// TRANSACTIONS
// ============================================================

class TransactionsPage extends StatelessWidget {
  const TransactionsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Transactions'),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.filter_list),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Row(
                children: [
                  Expanded(
                    child: _summary(
                      'Contributions',
                      '18,000 ETB',
                    ),
                  ),
                  Expanded(
                    child: _summary(
                      'Payouts',
                      '15,000 ETB',
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          ...transactions.map(
            (transaction) => Card(
              child: ListTile(
                leading: CircleAvatar(
                  child: Icon(
                    transaction.incoming
                        ? Icons.arrow_downward
                        : Icons.arrow_upward,
                  ),
                ),
                title: Text(transaction.title),
                subtitle: Text(
                  '${transaction.date} • ${transaction.type}',
                ),
                trailing: Text(
                  '${transaction.incoming ? '+' : '-'}'
                  '${_format(transaction.amount)} ETB',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: transaction.incoming
                        ? Colors.green
                        : Colors.redAccent,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _summary(String title, String value) {
    return Column(
      children: [
        Text(
          title,
          style: const TextStyle(
            color: Colors.grey,
          ),
        ),
        const SizedBox(height: 5),
        Text(
          value,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 17,
          ),
        ),
      ],
    );
  }
}

// ============================================================
// PROFILE
// ============================================================

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Profile'),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.edit),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const SizedBox(height: 10),

          const Center(
            child: CircleAvatar(
              radius: 45,
              child: Icon(
                Icons.person,
                size: 50,
              ),
            ),
          ),

          const SizedBox(height: 12),

          const Center(
            child: Text(
              'Kidane Desta',
              style: TextStyle(
                fontSize: 23,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),

          const Center(
            child: Text(
              'Equb Member',
              style: TextStyle(
                color: Colors.grey,
              ),
            ),
          ),

          const SizedBox(height: 25),

          Card(
            child: Column(
              children: [
                _profileItem(
                  Icons.phone,
                  'Phone',
                  '09XX XXX XXX',
                ),
                _profileItem(
                  Icons.badge,
                  'Member ID',
                  'EQB-000001',
                ),
                _profileItem(
                  Icons.calendar_month,
                  'Joined',
                  'January 2026',
                ),
                _profileItem(
                  Icons.account_balance,
                  'Equb',
                  'Aksum Community Equb',
                ),
              ],
            ),
          ),

          const SizedBox(height: 15),

          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.security),
                  title: const Text('Security'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
                ListTile(
                  leading: const Icon(Icons.notifications),
                  title: const Text('Notifications'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
                ListTile(
                  leading: const Icon(Icons.language),
                  title: const Text('Language'),
                  trailing: const Text('English'),
                  onTap: () {},
                ),
                ListTile(
                  leading: const Icon(Icons.info_outline),
                  title: const Text('About IDFS Equb'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
              ],
            ),
          ),

          const SizedBox(height: 15),

          OutlinedButton.icon(
            onPressed: () {},
            icon: const Icon(Icons.logout),
            label: const Text('Sign Out'),
          ),
        ],
      ),
    );
  }

  Widget _profileItem(
    IconData icon,
    String title,
    String value,
  ) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(value),
    );
  }
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

String _format(double value) {
  return value
      .toStringAsFixed(0)
      .replaceAllMapped(
        RegExp(r'\B(?=(\d{3})+(?!\d))'),
        (match) => ',',
      );
}
