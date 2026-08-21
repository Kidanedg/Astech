import 'package:flutter/material.dart';

void main() {
  runApp(const IddirApp());
}

// ============================================================
// IDFS IDDIR MOBILE APPLICATION
// Indigenous Digital Financial System
// Iddir App Management System
//
// Mobile counterpart of iddirweb.py
// ============================================================

class IddirApp extends StatelessWidget {
  const IddirApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IDFS Iddir',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF163A5F),
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: const Color(0xFFF5F7FA),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF163A5F),
          foregroundColor: Colors.white,
          elevation: 0,
          centerTitle: false,
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          margin: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 6,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
            side: const BorderSide(
              color: Color(0xFFE2E8F0),
            ),
          ),
        ),
      ),
      home: const LoginScreen(),
    );
  }
}

// ============================================================
// GLOBAL DATA MODELS
// ============================================================

class Member {
  String memberNo;
  String fullName;
  String householdNo;
  String phone;
  String sex;
  String branch;
  String occupation;
  double contribution;
  String frequency;
  double trustScore;
  String status;

  Member({
    required this.memberNo,
    required this.fullName,
    required this.householdNo,
    required this.phone,
    required this.sex,
    required this.branch,
    required this.occupation,
    required this.contribution,
    required this.frequency,
    required this.trustScore,
    required this.status,
  });
}

class IddirGroup {
  String code;
  String name;
  String branch;
  double contribution;
  String frequency;
  int capacity;
  double emergencyFund;
  double propertyValue;
  String status;

  IddirGroup({
    required this.code,
    required this.name,
    required this.branch,
    required this.contribution,
    required this.frequency,
    required this.capacity,
    required this.emergencyFund,
    required this.propertyValue,
    required this.status,
  });
}

class Contribution {
  String date;
  String group;
  String member;
  double amount;
  String method;
  String reference;
  String status;

  Contribution({
    required this.date,
    required this.group,
    required this.member,
    required this.amount,
    required this.method,
    required this.reference,
    required this.status,
  });
}

class Benefit {
  String date;
  String group;
  String member;
  String type;
  double approved;
  double paid;
  String status;

  Benefit({
    required this.date,
    required this.group,
    required this.member,
    required this.type,
    required this.approved,
    required this.paid,
    required this.status,
  });
}

class CommunityEvent {
  String date;
  String group;
  String type;
  int participants;
  double estimated;
  double actual;
  String status;

  CommunityEvent({
    required this.date,
    required this.group,
    required this.type,
    required this.participants,
    required this.estimated,
    required this.actual,
    required this.status,
  });
}

class CommunityProperty {
  String name;
  String type;
  String group;
  double acquisitionCost;
  double currentValue;
  double quantity;
  String condition;
  String ownership;
  String location;

  CommunityProperty({
    required this.name,
    required this.type,
    required this.group,
    required this.acquisitionCost,
    required this.currentValue,
    required this.quantity,
    required this.condition,
    required this.ownership,
    required this.location,
  });
}

class FinancialTransaction {
  String date;
  String branch;
  String group;
  String type;
  double amount;
  String reference;
  String description;

  FinancialTransaction({
    required this.date,
    required this.branch,
    required this.group,
    required this.type,
    required this.amount,
    required this.reference,
    required this.description,
  });
}

// ============================================================
// APPLICATION STATE
// ============================================================

class AppState extends ChangeNotifier {
  static final AppState instance = AppState._();

  AppState._();

  String userName = 'Iddir Administrator';
  String role = 'Administrator';

  final List<String> branches = [
    'IDR-001 | Iddir Central Branch',
    'IDR-002 | Iddir North Branch',
  ];

  final List<Member> members = [
    Member(
      memberNo: 'IDR-M001',
      fullName: 'Demo Member One',
      householdNo: 'HH-001',
      phone: '0911000000',
      sex: 'Male',
      branch: 'IDR-001 | Iddir Central Branch',
      occupation: 'Farmer',
      contribution: 100,
      frequency: 'Monthly',
      trustScore: .80,
      status: 'Active',
    ),
    Member(
      memberNo: 'IDR-M002',
      fullName: 'Demo Member Two',
      householdNo: 'HH-002',
      phone: '0922000000',
      sex: 'Female',
      branch: 'IDR-001 | Iddir Central Branch',
      occupation: 'Teacher',
      contribution: 100,
      frequency: 'Monthly',
      trustScore: .90,
      status: 'Active',
    ),
  ];

  final List<IddirGroup> groups = [
    IddirGroup(
      code: 'IDG-001',
      name: 'Aksum Community Iddir',
      branch: 'IDR-001 | Iddir Central Branch',
      contribution: 100,
      frequency: 'Monthly',
      capacity: 100,
      emergencyFund: 5000,
      propertyValue: 25000,
      status: 'Active',
    ),
  ];

  final List<Contribution> contributions = [];

  final List<Benefit> benefits = [];

  final List<CommunityEvent> events = [];

  final List<CommunityProperty> properties = [];

  final List<FinancialTransaction> transactions = [];

  int get activeMembers =>
      members.where((m) => m.status == 'Active').length;

  int get activeGroups =>
      groups.where((g) => g.status == 'Active').length;

  double get totalContributions =>
      contributions.fold(0, (sum, x) => sum + x.amount);

  double get totalBenefits =>
      benefits.fold(0, (sum, x) => sum + x.paid);

  double get totalPropertyValue =>
      properties.fold(
        0,
        (sum, x) => sum + x.currentValue * x.quantity,
      );

  double get totalEmergencyFunds =>
      groups.fold(0, (sum, x) => sum + x.emergencyFund);

  void addMember(Member member) {
    members.add(member);
    notifyListeners();
  }

  void addGroup(IddirGroup group) {
    groups.add(group);
    notifyListeners();
  }

  void addContribution(Contribution contribution) {
    contributions.add(contribution);
    notifyListeners();
  }

  void addBenefit(Benefit benefit) {
    benefits.add(benefit);
    notifyListeners();
  }

  void addEvent(CommunityEvent event) {
    events.add(event);
    notifyListeners();
  }

  void addProperty(CommunityProperty property) {
    properties.add(property);
    notifyListeners();
  }

  void addTransaction(FinancialTransaction transaction) {
    transactions.add(transaction);
    notifyListeners();
  }
}

// ============================================================
// LOGIN
// ============================================================

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final usernameController =
      TextEditingController(text: 'admin');

  final passwordController =
      TextEditingController(text: 'admin123');

  bool obscure = true;

  void login() {
    if (usernameController.text.trim() == 'admin' &&
        passwordController.text == 'admin123') {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => const MainShell(),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Invalid username or password.'),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxWidth: 460,
              ),
              child: Column(
                children: [
                  Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      color: const Color(0xFF163A5F),
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: const Icon(
                      Icons.groups_rounded,
                      color: Colors.white,
                      size: 48,
                    ),
                  ),
                  const SizedBox(height: 22),
                  const Text(
                    'IDFS Iddir',
                    style: TextStyle(
                      fontSize: 30,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF163A5F),
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Iddir App Management System',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.blueGrey,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 36),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        children: [
                          TextField(
                            controller: usernameController,
                            decoration: const InputDecoration(
                              labelText: 'Username',
                              prefixIcon:
                                  Icon(Icons.person_outline),
                              border: OutlineInputBorder(),
                            ),
                          ),
                          const SizedBox(height: 14),
                          TextField(
                            controller: passwordController,
                            obscureText: obscure,
                            decoration: InputDecoration(
                              labelText: 'Password',
                              prefixIcon:
                                  const Icon(Icons.lock_outline),
                              suffixIcon: IconButton(
                                onPressed: () {
                                  setState(() {
                                    obscure = !obscure;
                                  });
                                },
                                icon: Icon(
                                  obscure
                                      ? Icons.visibility
                                      : Icons.visibility_off,
                                ),
                              ),
                              border: const OutlineInputBorder(),
                            ),
                          ),
                          const SizedBox(height: 20),
                          SizedBox(
                            width: double.infinity,
                            child: FilledButton.icon(
                              onPressed: login,
                              icon: const Icon(Icons.login),
                              label: const Text('Sign In'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Demonstration account: admin / admin123',
                    style: TextStyle(
                      color: Colors.blueGrey,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ============================================================
// MAIN SHELL
// ============================================================

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int selectedIndex = 0;

  final List<Widget> screens = const [
    DashboardScreen(),
    MembersScreen(),
    ContributionsScreen(),
    GroupsScreen(),
    MoreScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppState.instance,
      builder: (context, _) {
        return Scaffold(
          body: screens[selectedIndex],
          bottomNavigationBar: NavigationBar(
            selectedIndex: selectedIndex,
            onDestinationSelected: (index) {
              setState(() {
                selectedIndex = index;
              });
            },
            destinations: const [
              NavigationDestination(
                icon: Icon(Icons.dashboard_outlined),
                selectedIcon: Icon(Icons.dashboard),
                label: 'Home',
              ),
              NavigationDestination(
                icon: Icon(Icons.people_outline),
                selectedIcon: Icon(Icons.people),
                label: 'Members',
              ),
              NavigationDestination(
                icon: Icon(Icons.payments_outlined),
                selectedIcon: Icon(Icons.payments),
                label: 'Payments',
              ),
              NavigationDestination(
                icon: Icon(Icons.groups_outlined),
                selectedIcon: Icon(Icons.groups),
                label: 'Groups',
              ),
              NavigationDestination(
                icon: Icon(Icons.apps_outlined),
                selectedIcon: Icon(Icons.apps),
                label: 'More',
              ),
            ],
          ),
        );
      },
    );
  }
}

// ============================================================
// COMMON APP BAR
// ============================================================

PreferredSizeWidget appBar(
  String title, {
  String? subtitle,
  List<Widget>? actions,
}) {
  return AppBar(
    title: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
        if (subtitle != null)
          Text(
            subtitle,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.normal,
            ),
          ),
      ],
    ),
    actions: actions,
  );
}

// ============================================================
// DASHBOARD
// ============================================================

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    return Scaffold(
      appBar: appBar(
        'Iddir Dashboard',
        subtitle: 'Indigenous Digital Financial System',
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.notifications_none),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await Future.delayed(
            const Duration(milliseconds: 400),
          );
        },
        child: ListView(
          padding: const EdgeInsets.only(
            top: 12,
            bottom: 20,
          ),
          children: [
            Padding(
              padding:
                  const EdgeInsets.symmetric(horizontal: 14),
              child: Text(
                'Welcome, ${state.userName}',
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF163A5F),
                ),
              ),
            ),
            const SizedBox(height: 4),
            const Padding(
              padding:
                  EdgeInsets.symmetric(horizontal: 14),
              child: Text(
                'Community mutual-support and financial management',
                style: TextStyle(
                  color: Colors.blueGrey,
                ),
              ),
            ),
            const SizedBox(height: 16),

            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              padding: const EdgeInsets.symmetric(
                horizontal: 10,
              ),
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              childAspectRatio: 1.45,
              children: [
                metricCard(
                  'Active Members',
                  '${state.activeMembers}',
                  Icons.people,
                ),
                metricCard(
                  'Iddir Groups',
                  '${state.activeGroups}',
                  Icons.groups,
                ),
                metricCard(
                  'Contributions',
                  money(state.totalContributions),
                  Icons.account_balance_wallet,
                ),
                metricCard(
                  'Property Value',
                  money(state.totalPropertyValue),
                  Icons.home_work,
                ),
              ],
            ),

            const SizedBox(height: 14),

            sectionTitle(
              'Community Financial Position',
            ),

            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    summaryRow(
                      'Contributions',
                      money(state.totalContributions),
                      Icons.arrow_downward,
                      Colors.green,
                    ),
                    const Divider(),
                    summaryRow(
                      'Benefits Paid',
                      money(state.totalBenefits),
                      Icons.arrow_upward,
                      Colors.orange,
                    ),
                    const Divider(),
                    summaryRow(
                      'Emergency Funds',
                      money(state.totalEmergencyFunds),
                      Icons.shield_outlined,
                      Colors.blue,
                    ),
                  ],
                ),
              ),
            ),

            sectionTitle('Quick Access'),

            GridView.count(
              crossAxisCount: 3,
              shrinkWrap: true,
              physics:
                  const NeverScrollableScrollPhysics(),
              padding: const EdgeInsets.symmetric(
                horizontal: 10,
              ),
              children: [
                quickAction(
                  context,
                  'Member',
                  Icons.person_add_alt_1,
                  const MembersScreen(),
                ),
                quickAction(
                  context,
                  'Contribution',
                  Icons.payments,
                  const ContributionsScreen(),
                ),
                quickAction(
                  context,
                  'Benefit',
                  Icons.volunteer_activism,
                  const BenefitsScreen(),
                ),
                quickAction(
                  context,
                  'Event',
                  Icons.event,
                  const EventsScreen(),
                ),
                quickAction(
                  context,
                  'Property',
                  Icons.business,
                  const PropertyScreen(),
                ),
                quickAction(
                  context,
                  'Reports',
                  Icons.analytics,
                  const ReportsScreen(),
                ),
              ],
            ),

            sectionTitle('System Modules'),

            Card(
              child: Column(
                children: [
                  moduleTile(
                    context,
                    'Fund Sustainability',
                    'Contributions, benefits and fund balance',
                    Icons.trending_up,
                    const FundScreen(),
                  ),
                  moduleTile(
                    context,
                    'Statistical Models',
                    'Eligibility and contribution-risk indicators',
                    Icons.query_stats,
                    const StatisticalScreen(),
                  ),
                  moduleTile(
                    context,
                    'Financial Transactions',
                    'Financial recording and reconciliation',
                    Icons.receipt_long,
                    const TransactionsScreen(),
                  ),
                  moduleTile(
                    context,
                    'Audit Trail',
                    'Traceable system activities',
                    Icons.fact_check_outlined,
                    const AuditScreen(),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================
// MEMBERS
// ============================================================

class MembersScreen extends StatefulWidget {
  const MembersScreen({super.key});

  @override
  State<MembersScreen> createState() =>
      _MembersScreenState();
}

class _MembersScreenState extends State<MembersScreen> {
  String search = '';

  @override
  Widget build(BuildContext context) {
    final all = AppState.instance.members;

    final list = all.where((m) {
      final q = search.toLowerCase();
      return m.fullName.toLowerCase().contains(q) ||
          m.memberNo.toLowerCase().contains(q) ||
          m.phone.toLowerCase().contains(q);
    }).toList();

    return Scaffold(
      appBar: appBar(
        'Members',
        subtitle: '${all.length} registered members',
        actions: [
          IconButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const AddMemberScreen(),
                ),
              );
            },
            icon: const Icon(Icons.person_add),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              onChanged: (value) {
                setState(() {
                  search = value;
                });
              },
              decoration: InputDecoration(
                hintText: 'Search member...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: search.isNotEmpty
                    ? IconButton(
                        onPressed: () {
                          setState(() {
                            search = '';
                          });
                        },
                        icon: const Icon(Icons.clear),
                      )
                    : null,
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          Expanded(
            child: list.isEmpty
                ? const Center(
                    child: Text('No members found.'),
                  )
                : ListView.builder(
                    itemCount: list.length,
                    itemBuilder: (context, index) {
                      final m = list[index];

                      return Card(
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor:
                                const Color(0xFFE6EEF6),
                            child: Text(
                              m.fullName.isNotEmpty
                                  ? m.fullName[0]
                                  : '?',
                              style: const TextStyle(
                                color: Color(0xFF163A5F),
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          title: Text(
                            m.fullName,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          subtitle: Text(
                            '${m.memberNo} • ${m.phone}\n'
                            '${m.frequency} • ${money(m.contribution)}',
                          ),
                          isThreeLine: true,
                          trailing: statusChip(m.status),
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) =>
                                    MemberDetailScreen(
                                  member: m,
                                ),
                              ),
                            );
                          },
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => const AddMemberScreen(),
            ),
          );
        },
        icon: const Icon(Icons.add),
        label: const Text('Member'),
      ),
    );
  }
}

// ============================================================
// ADD MEMBER
// ============================================================

class AddMemberScreen extends StatefulWidget {
  const AddMemberScreen({super.key});

  @override
  State<AddMemberScreen> createState() =>
      _AddMemberScreenState();
}

class _AddMemberScreenState
    extends State<AddMemberScreen> {
  final no = TextEditingController();
  final name = TextEditingController();
  final household = TextEditingController();
  final phone = TextEditingController();
  final occupation = TextEditingController();
  final amount = TextEditingController(text: '100');

  String sex = 'Not Specified';
  String frequency = 'Monthly';
  String branch =
      'IDR-001 | Iddir Central Branch';

  void save() {
    if (no.text.trim().isEmpty ||
        name.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Member number and full name are required.',
          ),
        ),
      );
      return;
    }

    AppState.instance.addMember(
      Member(
        memberNo: no.text.trim(),
        fullName: name.text.trim(),
        householdNo: household.text.trim(),
        phone: phone.text.trim(),
        sex: sex,
        branch: branch,
        occupation: occupation.text.trim(),
        contribution:
            double.tryParse(amount.text) ?? 0,
        frequency: frequency,
        trustScore: .50,
        status: 'Active',
      ),
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar('Register Member'),
      body: Form(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            textField(no, 'Member Number'),
            textField(name, 'Full Name'),
            textField(
              household,
              'Household Number',
            ),
            textField(
              phone,
              'Phone',
              keyboard: TextInputType.phone,
            ),
            dropdown(
              'Sex',
              sex,
              [
                'Not Specified',
                'Male',
                'Female',
              ],
              (v) => setState(() => sex = v),
            ),
            dropdown(
              'Branch',
              branch,
              AppState.instance.branches,
              (v) => setState(() => branch = v),
            ),
            textField(
              occupation,
              'Occupation',
            ),
            textField(
              amount,
              'Regular Contribution (ETB)',
              keyboard: TextInputType.number,
            ),
            dropdown(
              'Contribution Frequency',
              frequency,
              [
                'Monthly',
                'Quarterly',
                'Weekly',
                'Annual',
                'Custom',
              ],
              (v) =>
                  setState(() => frequency = v),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: save,
              icon: const Icon(Icons.save),
              label: const Text(
                'Register Member',
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================
// MEMBER DETAIL
// ============================================================

class MemberDetailScreen extends StatelessWidget {
  final Member member;

  const MemberDetailScreen({
    super.key,
    required this.member,
  });

  @override
  Widget build(BuildContext context) {
    final contributions = AppState.instance
        .contributions
        .where((x) => x.member == member.memberNo)
        .toList();

    final total = contributions.fold<double>(
      0,
      (sum, x) => sum + x.amount,
    );

    return Scaffold(
      appBar: appBar(
        'Member Profile',
        subtitle: member.memberNo,
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 35,
                    backgroundColor:
                        const Color(0xFFE6EEF6),
                    child: Text(
                      member.fullName[0],
                      style: const TextStyle(
                        fontSize: 28,
                        color: Color(0xFF163A5F),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    member.fullName,
                    style: const TextStyle(
                      fontSize: 21,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(member.memberNo),
                  const SizedBox(height: 12),
                  statusChip(member.status),
                ],
              ),
            ),
          ),
          metricRow(
            'Planned Contribution',
            money(member.contribution),
          ),
          metricRow(
            'Total Paid',
            money(total),
          ),
          metricRow(
            'Trust Score',
            '${(member.trustScore * 100).toStringAsFixed(0)}%',
          ),
          metricRow(
            'Frequency',
            member.frequency,
          ),
          metricRow(
            'Household',
            member.householdNo,
          ),
          metricRow(
            'Phone',
            member.phone,
          ),
          metricRow(
            'Occupation',
            member.occupation,
          ),
          sectionTitle('Contribution History'),
          if (contributions.isEmpty)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(18),
                child: Text(
                  'No contribution records.',
                ),
              ),
            ),
          ...contributions.map(
            (c) => Card(
              child: ListTile(
                leading: const Icon(
                  Icons.payments,
                  color: Colors.green,
                ),
                title: Text(money(c.amount)),
                subtitle:
                    Text('${c.date} • ${c.method}'),
                trailing: statusChip(c.status),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// GROUPS
// ============================================================

class GroupsScreen extends StatelessWidget {
  const GroupsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final groups = AppState.instance.groups;

    return Scaffold(
      appBar: appBar(
        'Iddir Groups',
        subtitle: '${groups.length} groups',
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(
          vertical: 8,
        ),
        children: [
          ...groups.map(
            (g) => Card(
              child: ExpansionTile(
                leading: CircleAvatar(
                  backgroundColor:
                      const Color(0xFFE6EEF6),
                  child: const Icon(
                    Icons.groups,
                    color: Color(0xFF163A5F),
                  ),
                ),
                title: Text(
                  g.name,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                subtitle: Text(
                  '${g.code} • ${g.branch}',
                ),
                childrenPadding:
                    const EdgeInsets.all(16),
                children: [
                  metricRow(
                    'Contribution',
                    money(g.contribution),
                  ),
                  metricRow(
                    'Frequency',
                    g.frequency,
                  ),
                  metricRow(
                    'Capacity',
                    '${g.capacity}',
                  ),
                  metricRow(
                    'Emergency Fund',
                    money(g.emergencyFund),
                  ),
                  metricRow(
                    'Property Value',
                    money(g.propertyValue),
                  ),
                  statusChip(g.status),
                ],
              ),
            ),
          ),
        ],
      ),
      floatingActionButton:
          FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) =>
                  const AddGroupScreen(),
            ),
          );
        },
        icon: const Icon(Icons.add),
        label: const Text('Group'),
      ),
    );
  }
}

// ============================================================
// ADD GROUP
// ============================================================

class AddGroupScreen extends StatefulWidget {
  const AddGroupScreen({super.key});

  @override
  State<AddGroupScreen> createState() =>
      _AddGroupScreenState();
}

class _AddGroupScreenState
    extends State<AddGroupScreen> {
  final code = TextEditingController();
  final name = TextEditingController();
  final amount =
      TextEditingController(text: '100');
  final capacity =
      TextEditingController(text: '100');

  String branch =
      'IDR-001 | Iddir Central Branch';

  String frequency = 'Monthly';

  void save() {
    if (code.text.trim().isEmpty ||
        name.text.trim().isEmpty) {
      return;
    }

    AppState.instance.addGroup(
      IddirGroup(
        code: code.text.trim(),
        name: name.text.trim(),
        branch: branch,
        contribution:
            double.tryParse(amount.text) ?? 0,
        frequency: frequency,
        capacity:
            int.tryParse(capacity.text) ?? 0,
        emergencyFund: 0,
        propertyValue: 0,
        status: 'Active',
      ),
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar('Register Iddir Group'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          textField(code, 'Group Code'),
          textField(name, 'Group Name'),
          dropdown(
            'Branch',
            branch,
            AppState.instance.branches,
            (v) => setState(() => branch = v),
          ),
          textField(
            amount,
            'Regular Contribution (ETB)',
            keyboard: TextInputType.number,
          ),
          dropdown(
            'Contribution Frequency',
            frequency,
            [
              'Monthly',
              'Quarterly',
              'Weekly',
              'Annual',
            ],
            (v) =>
                setState(() => frequency = v),
          ),
          textField(
            capacity,
            'Member Capacity',
            keyboard: TextInputType.number,
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: save,
            icon: const Icon(Icons.save),
            label: const Text(
              'Register Iddir Group',
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// CONTRIBUTIONS
// ============================================================

class ContributionsScreen extends StatefulWidget {
  const ContributionsScreen({super.key});

  @override
  State<ContributionsScreen> createState() =>
      _ContributionsScreenState();
}

class _ContributionsScreenState
    extends State<ContributionsScreen> {
  void add() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) =>
            const AddContributionScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final list = AppState.instance.contributions;

    return Scaffold(
      appBar: appBar(
        'Contributions',
        subtitle:
            '${money(AppState.instance.totalContributions)} collected',
      ),
      body: list.isEmpty
          ? const EmptyState(
              icon: Icons.payments_outlined,
              title: 'No contributions yet',
              message:
                  'Record the first member contribution.',
            )
          : ListView.builder(
              padding: const EdgeInsets.only(
                top: 8,
                bottom: 90,
              ),
              itemCount: list.length,
              itemBuilder: (context, index) {
                final c = list[
                  list.length - 1 - index
                ];

                return Card(
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor:
                          Colors.green.shade50,
                      child: const Icon(
                        Icons.payments,
                        color: Colors.green,
                      ),
                    ),
                    title: Text(
                      money(c.amount),
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    subtitle: Text(
                      '${c.member} • ${c.group}\n'
                      '${c.date} • ${c.method}',
                    ),
                    isThreeLine: true,
                    trailing:
                        statusChip(c.status),
                  ),
                );
              },
            ),
      floatingActionButton:
          FloatingActionButton.extended(
        onPressed: add,
        icon: const Icon(Icons.add),
        label: const Text('Contribution'),
      ),
    );
  }
}

// ============================================================
// ADD CONTRIBUTION
// ============================================================

class AddContributionScreen
    extends StatefulWidget {
  const AddContributionScreen({super.key});

  @override
  State<AddContributionScreen> createState() =>
      _AddContributionScreenState();
}

class _AddContributionScreenState
    extends State<AddContributionScreen> {
  String member = '';
  String group = '';
  String method = 'Cash';

  final amount =
      TextEditingController();

  final reference =
      TextEditingController();

  @override
  void initState() {
    super.initState();

    if (AppState.instance.members.isNotEmpty) {
      member =
          AppState.instance.members.first.memberNo;
    }

    if (AppState.instance.groups.isNotEmpty) {
      group =
          AppState.instance.groups.first.code;
    }

    amount.text =
        AppState.instance.groups.isNotEmpty
            ? AppState.instance.groups.first
                .contribution
                .toString()
            : '100';
  }

  void save() {
    final value =
        double.tryParse(amount.text) ?? 0;

    if (value <= 0) return;

    AppState.instance.addContribution(
      Contribution(
        date: today(),
        group: group,
        member: member,
        amount: value,
        method: method,
        reference: reference.text,
        status: 'Paid',
      ),
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final members =
        AppState.instance.members;
    final groups =
        AppState.instance.groups;

    return Scaffold(
      appBar: appBar('Record Contribution'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          dropdown(
            'Member',
            member,
            members.map((m) => m.memberNo).toList(),
            (v) => setState(() => member = v),
          ),
          dropdown(
            'Iddir Group',
            group,
            groups.map((g) => g.code).toList(),
            (v) => setState(() => group = v),
          ),
          textField(
            amount,
            'Contribution Amount (ETB)',
            keyboard: TextInputType.number,
          ),
          dropdown(
            'Payment Method',
            method,
            [
              'Cash',
              'Bank Transfer',
              'Mobile Money',
              'Other',
            ],
            (v) => setState(() => method = v),
          ),
          textField(
            reference,
            'Reference',
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: save,
            icon: const Icon(Icons.check_circle),
            label: const Text(
              'Record Contribution',
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// BENEFITS
// ============================================================

class BenefitsScreen extends StatefulWidget {
  const BenefitsScreen({super.key});

  @override
  State<BenefitsScreen> createState() =>
      _BenefitsScreenState();
}

class _BenefitsScreenState
    extends State<BenefitsScreen> {
  @override
  Widget build(BuildContext context) {
    final list = AppState.instance.benefits;

    return Scaffold(
      appBar: appBar(
        'Benefits & Mutual Support',
        subtitle:
            money(AppState.instance.totalBenefits),
      ),
      body: list.isEmpty
          ? const EmptyState(
              icon: Icons.volunteer_activism,
              title: 'No benefit records',
              message:
                  'Community support records will appear here.',
            )
          : ListView.builder(
              itemCount: list.length,
              itemBuilder: (context, index) {
                final b =
                    list[list.length - 1 - index];

                return Card(
                  child: ListTile(
                    leading: const CircleAvatar(
                      child: Icon(
                        Icons.volunteer_activism,
                      ),
                    ),
                    title: Text(b.type),
                    subtitle: Text(
                      '${b.member} • ${b.group}\n'
                      '${b.date} • Paid ${money(b.paid)}',
                    ),
                    isThreeLine: true,
                    trailing:
                        statusChip(b.status),
                  ),
                );
              },
            ),
      floatingActionButton:
          FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) =>
                  const AddBenefitScreen(),
            ),
          );
        },
        icon: const Icon(Icons.add),
        label: const Text('Benefit'),
      ),
    );
  }
}

// ============================================================
// ADD BENEFIT
// ============================================================

class AddBenefitScreen extends StatefulWidget {
  const AddBenefitScreen({super.key});

  @override
  State<AddBenefitScreen> createState() =>
      _AddBenefitScreenState();
}

class _AddBenefitScreenState
    extends State<AddBenefitScreen> {
  String member = '';
  String group = '';
  String type =
      'Bereavement Support';

  String status = 'Requested';

  final approved =
      TextEditingController();

  final paid =
      TextEditingController();

  @override
  void initState() {
    super.initState();

    if (AppState.instance.members.isNotEmpty) {
      member =
          AppState.instance.members.first.memberNo;
    }

    if (AppState.instance.groups.isNotEmpty) {
      group =
          AppState.instance.groups.first.code;
    }
  }

  void save() {
    AppState.instance.addBenefit(
      Benefit(
        date: today(),
        group: group,
        member: member,
        type: type,
        approved:
            double.tryParse(approved.text) ?? 0,
        paid: double.tryParse(paid.text) ?? 0,
        status: status,
      ),
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar(
        'Community Support',
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          dropdown(
            'Iddir Group',
            group,
            AppState.instance.groups
                .map((g) => g.code)
                .toList(),
            (v) => setState(() => group = v),
          ),
          dropdown(
            'Beneficiary Member',
            member,
            AppState.instance.members
                .map((m) => m.memberNo)
                .toList(),
            (v) => setState(() => member = v),
          ),
          dropdown(
            'Benefit Type',
            type,
            [
              'Bereavement Support',
              'Funeral Support',
              'Emergency Medical Support',
              'Emergency Household Support',
              'Natural Disaster Support',
              'Other Community Support',
            ],
            (v) => setState(() => type = v),
          ),
          textField(
            approved,
            'Approved Amount (ETB)',
            keyboard: TextInputType.number,
          ),
          textField(
            paid,
            'Paid Amount (ETB)',
            keyboard: TextInputType.number,
          ),
          dropdown(
            'Status',
            status,
            [
              'Requested',
              'Reviewed',
              'Approved',
              'Paid',
              'Rejected',
            ],
            (v) => setState(() => status = v),
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: save,
            icon: const Icon(Icons.save),
            label: const Text(
              'Save Benefit Record',
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// EVENTS
// ============================================================

class EventsScreen extends StatelessWidget {
  const EventsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final events = AppState.instance.events;

    return Scaffold(
      appBar: appBar(
        'Community Events',
        subtitle: 'Planning and costing',
      ),
      body: events.isEmpty
          ? const EmptyState(
              icon: Icons.event,
              title: 'No community events',
              message:
                  'Record meetings, funerals and community events.',
            )
          : ListView.builder(
              itemCount: events.length,
              itemBuilder: (context, index) {
                final e =
                    events[events.length - 1 - index];

                return Card(
                  child: ListTile(
                    leading:
                        const CircleAvatar(
                      child: Icon(Icons.event),
                    ),
                    title: Text(e.type),
                    subtitle: Text(
                      '${e.group} • ${e.date}\n'
                      '${e.participants} participants • '
                      'Actual ${money(e.actual)}',
                    ),
                    isThreeLine: true,
                    trailing:
                        statusChip(e.status),
                  ),
                );
              },
            ),
      floatingActionButton:
          FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) =>
                  const AddEventScreen(),
            ),
          );
        },
        icon: const Icon(Icons.add),
        label: const Text('Event'),
      ),
    );
  }
}

// ============================================================
// ADD EVENT
// ============================================================

class AddEventScreen extends StatefulWidget {
  const AddEventScreen({super.key});

  @override
  State<AddEventScreen> createState() =>
      _AddEventScreenState();
}

class _AddEventScreenState
    extends State<AddEventScreen> {
  String group = '';
  String type = 'Community Meeting';
  String status = 'Planned';

  final participants =
      TextEditingController();

  final estimated =
      TextEditingController();

  final actual =
      TextEditingController();

  @override
  void initState() {
    super.initState();

    if (AppState.instance.groups.isNotEmpty) {
      group =
          AppState.instance.groups.first.code;
    }
  }

  void save() {
    AppState.instance.addEvent(
      CommunityEvent(
        date: today(),
        group: group,
        type: type,
        participants:
            int.tryParse(participants.text) ?? 0,
        estimated:
            double.tryParse(estimated.text) ?? 0,
        actual:
            double.tryParse(actual.text) ?? 0,
        status: status,
      ),
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar('Community Event'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          dropdown(
            'Iddir Group',
            group,
            AppState.instance.groups
                .map((g) => g.code)
                .toList(),
            (v) => setState(() => group = v),
          ),
          dropdown(
            'Event Type',
            type,
            [
              'Community Meeting',
              'Funeral',
              'Memorial',
              'Social Gathering',
              'Emergency Response',
              'Other',
            ],
            (v) => setState(() => type = v),
          ),
          textField(
            participants,
            'Households / Participants',
            keyboard: TextInputType.number,
          ),
          textField(
            estimated,
            'Estimated Cost (ETB)',
            keyboard: TextInputType.number,
          ),
          textField(
            actual,
            'Actual Cost (ETB)',
            keyboard: TextInputType.number,
          ),
          dropdown(
            'Status',
            status,
            [
              'Planned',
              'Active',
              'Completed',
              'Cancelled',
            ],
            (v) => setState(() => status = v),
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: save,
            icon: const Icon(Icons.save),
            label: const Text('Save Event'),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// PROPERTY
// ============================================================

class PropertyScreen extends StatelessWidget {
  const PropertyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final properties =
        AppState.instance.properties;

    return Scaffold(
      appBar: appBar(
        'Property Management',
        subtitle: 'Community assets',
      ),
      body: properties.isEmpty
          ? const EmptyState(
              icon: Icons.business,
              title: 'No properties registered',
              message:
                  'Community property will appear here.',
            )
          : ListView.builder(
              itemCount: properties.length,
              itemBuilder: (context, index) {
                final p = properties[index];

                return Card(
                  child: ListTile(
                    leading:
                        const CircleAvatar(
                      child: Icon(
                        Icons.business,
                      ),
                    ),
                    title: Text(p.name),
                    subtitle: Text(
                      '${p.type} • ${p.group}\n'
                      'Value ${money(p.currentValue)}',
                    ),
                    isThreeLine: true,
                    trailing: Text(
                      p.condition,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                );
              },
            ),
      floatingActionButton:
          FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) =>
                  const AddPropertyScreen(),
            ),
          );
        },
        icon: const Icon(Icons.add),
        label: const Text('Property'),
      ),
    );
  }
}

// ============================================================
// ADD PROPERTY
// ============================================================

class AddPropertyScreen extends StatefulWidget {
  const AddPropertyScreen({super.key});

  @override
  State<AddPropertyScreen> createState() =>
      _AddPropertyScreenState();
}

class _AddPropertyScreenState
    extends State<AddPropertyScreen> {
  final name = TextEditingController();
  final acquisition = TextEditingController();
  final current = TextEditingController();
  final quantity =
      TextEditingController(text: '1');
  final location = TextEditingController();

  String group = '';
  String type = 'Building';
  String condition = 'Good';
  String ownership = 'Community';

  @override
  void initState() {
    super.initState();

    if (AppState.instance.groups.isNotEmpty) {
      group =
          AppState.instance.groups.first.code;
    }
  }

  void save() {
    AppState.instance.addProperty(
      CommunityProperty(
        name: name.text,
        type: type,
        group: group,
        acquisitionCost:
            double.tryParse(acquisition.text) ?? 0,
        currentValue:
            double.tryParse(current.text) ?? 0,
        quantity:
            double.tryParse(quantity.text) ?? 1,
        condition: condition,
        ownership: ownership,
        location: location.text,
      ),
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar('Register Property'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          dropdown(
            'Iddir Group',
            group,
            AppState.instance.groups
                .map((g) => g.code)
                .toList(),
            (v) => setState(() => group = v),
          ),
          dropdown(
            'Property Type',
            type,
            [
              'Building',
              'Land',
              'Vehicle',
              'Equipment',
              'Furniture',
              'Funeral Equipment',
              'Community Asset',
              'Other',
            ],
            (v) => setState(() => type = v),
          ),
          textField(name, 'Property Name'),
          textField(
            acquisition,
            'Acquisition Cost (ETB)',
            keyboard: TextInputType.number,
          ),
          textField(
            current,
            'Current Value (ETB)',
            keyboard: TextInputType.number,
          ),
          textField(
            quantity,
            'Quantity',
            keyboard: TextInputType.number,
          ),
          dropdown(
            'Condition',
            condition,
            [
              'Excellent',
              'Good',
              'Fair',
              'Needs Repair',
              'Unusable',
            ],
            (v) => setState(() => condition = v),
          ),
          dropdown(
            'Ownership',
            ownership,
            [
              'Community',
              'Group',
              'Joint',
              'Other',
            ],
            (v) => setState(() => ownership = v),
          ),
          textField(location, 'Location'),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: save,
            icon: const Icon(Icons.save),
            label: const Text(
              'Register Property',
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// FUND SUSTAINABILITY
// ============================================================

class FundScreen extends StatelessWidget {
  const FundScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    final net =
        state.totalContributions -
            state.totalBenefits;

    return Scaffold(
      appBar: appBar(
        'Fund Sustainability',
        subtitle:
            'Contributions and community support',
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                children: [
                  const Icon(
                    Icons.account_balance,
                    size: 45,
                    color: Color(0xFF163A5F),
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'Net Fund Change',
                    style: TextStyle(
                      color: Colors.blueGrey,
                    ),
                  ),
                  Text(
                    money(net),
                    style: const TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF163A5F),
                    ),
                  ),
                ],
              ),
            ),
          ),
          metricRow(
            'Total Contributions',
            money(state.totalContributions),
          ),
          metricRow(
            'Total Benefits',
            money(state.totalBenefits),
          ),
          metricRow(
            'Emergency Funds',
            money(state.totalEmergencyFunds),
          ),
          const SizedBox(height: 14),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'F(t+1) = F(t) + C(t) + O(t) − B(t) − A(t)',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 17,
                  color: Color(0xFF163A5F),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// STATISTICAL MODELS
// ============================================================

class StatisticalScreen extends StatelessWidget {
  const StatisticalScreen({super.key});

  double consistency(Member member) {
    final records = AppState.instance.contributions
        .where(
          (x) => x.member == member.memberNo,
        )
        .toList();

    if (records.isEmpty) return 0;

    final paid = records
        .where((x) => x.status == 'Paid')
        .length;

    return paid / records.length;
  }

  @override
  Widget build(BuildContext context) {
    final members = AppState.instance.members;

    return Scaffold(
      appBar: appBar(
        'Statistical Models',
        subtitle:
            'Transparent analytical indicators',
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: const [
                  Text(
                    'Benefit Eligibility Score',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF163A5F),
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Eᵢ = w₁Cᵢ + w₂Pᵢ + w₃Tᵢ + w₄Mᵢ',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 17,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'The prototype combines contribution level, '
                    'payment consistency, trust and membership '
                    'duration as transparent indicators.',
                  ),
                ],
              ),
            ),
          ),

          sectionTitle(
            'Member Indicators',
          ),

          ...members.map((m) {
            final p = consistency(m);

            final score =
                .35 * contributionComponent(m) +
                .30 * p +
                .20 * m.trustScore +
                .15 * membershipComponent(m);

            return Card(
              child: ListTile(
                leading: CircleAvatar(
                  child: Text(
                    m.fullName[0],
                  ),
                ),
                title: Text(m.fullName),
                subtitle: Text(
                  'Payment consistency: '
                  '${(p * 100).toStringAsFixed(0)}%\n'
                  'Contribution risk: '
                  '${((1 - p) * 100).toStringAsFixed(0)}%',
                ),
                isThreeLine: true,
                trailing: Column(
                  mainAxisAlignment:
                      MainAxisAlignment.center,
                  children: [
                    const Text(
                      'Score',
                      style: TextStyle(
                        fontSize: 11,
                      ),
                    ),
                    Text(
                      '${(score * 100).toStringAsFixed(0)}%',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF163A5F),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),

          const SizedBox(height: 10),

          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Rᵢ = 1 − Pᵢ\n\n'
                'Higher contribution-risk values indicate '
                'a need for administrative follow-up, not '
                'a conclusion about the member.',
                style: const TextStyle(
                  height: 1.5,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

double contributionComponent(Member m) {
  final all = AppState.instance.members;

  final maxValue = all.fold<double>(
    0,
    (max, x) =>
        x.contribution > max
            ? x.contribution
            : max,
  );

  if (maxValue == 0) return 0;

  return m.contribution / maxValue;
}

double membershipComponent(Member m) {
  // Mobile prototype proxy.
  return .5;
}

// ============================================================
// TRANSACTIONS
// ============================================================

class TransactionsScreen extends StatelessWidget {
  const TransactionsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final transactions =
        AppState.instance.transactions;

    return Scaffold(
      appBar: appBar(
        'Financial Transactions',
        subtitle: 'Recording and reconciliation',
      ),
      body: transactions.isEmpty
          ? const EmptyState(
              icon: Icons.receipt_long,
              title: 'No transactions',
              message:
                  'Financial transactions will appear here.',
            )
          : ListView.builder(
              itemCount: transactions.length,
              itemBuilder: (context, index) {
                final t =
                    transactions[index];

                return Card(
                  child: ListTile(
                    leading:
                        const CircleAvatar(
                      child: Icon(
                        Icons.receipt_long,
                      ),
                    ),
                    title: Text(
                      t.type,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    subtitle: Text(
                      '${t.date} • ${t.group}\n'
                      '${t.reference}',
                    ),
                    isThreeLine: true,
                    trailing: Text(
                      money(t.amount),
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                );
              },
            ),
      floatingActionButton:
          FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) =>
                  const AddTransactionScreen(),
            ),
          );
        },
        icon: const Icon(Icons.add),
        label: const Text('Transaction'),
      ),
    );
  }
}

// ============================================================
// ADD TRANSACTION
// ============================================================

class AddTransactionScreen
    extends StatefulWidget {
  const AddTransactionScreen({super.key});

  @override
  State<AddTransactionScreen> createState() =>
      _AddTransactionScreenState();
}

class _AddTransactionScreenState
    extends State<AddTransactionScreen> {
  String branch =
      'IDR-001 | Iddir Central Branch';

  String group = '';

  String type = 'Contribution';

  final amount = TextEditingController();

  final reference =
      TextEditingController();

  final description =
      TextEditingController();

  @override
  void initState() {
    super.initState();

    if (AppState.instance.groups.isNotEmpty) {
      group =
          AppState.instance.groups.first.code;
    }
  }

  void save() {
    AppState.instance.addTransaction(
      FinancialTransaction(
        date: today(),
        branch: branch,
        group: group,
        type: type,
        amount:
            double.tryParse(amount.text) ?? 0,
        reference: reference.text,
        description: description.text,
      ),
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar(
        'Record Transaction',
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          dropdown(
            'Branch',
            branch,
            AppState.instance.branches,
            (v) => setState(() => branch = v),
          ),
          dropdown(
            'Iddir Group',
            group,
            AppState.instance.groups
                .map((g) => g.code)
                .toList(),
            (v) => setState(() => group = v),
          ),
          dropdown(
            'Transaction Type',
            type,
            [
              'Contribution',
              'Benefit Payment',
              'Property Purchase',
              'Property Sale',
              'Donation',
              'Administrative Expense',
              'Adjustment',
              'Other',
            ],
            (v) => setState(() => type = v),
          ),
          textField(
            amount,
            'Amount (ETB)',
            keyboard: TextInputType.number,
          ),
          textField(
            reference,
            'Reference',
          ),
          textField(
            description,
            'Description',
            maxLines: 3,
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: save,
            icon: const Icon(Icons.save),
            label: const Text(
              'Record Transaction',
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// REPORTS
// ============================================================

class ReportsScreen extends StatelessWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    return Scaffold(
      appBar: appBar(
        'Reports & Analytics',
        subtitle: 'Iddir management information',
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          reportCard(
            'Module Summary',
            Icons.dashboard,
            [
              'Active Members: ${state.activeMembers}',
              'Active Groups: ${state.activeGroups}',
              'Contributions: ${money(state.totalContributions)}',
              'Benefits Paid: ${money(state.totalBenefits)}',
              'Property Value: ${money(state.totalPropertyValue)}',
            ],
          ),
          reportCard(
            'Member Report',
            Icons.people,
            [
              'Registered members: ${state.members.length}',
              'Active members: ${state.activeMembers}',
            ],
          ),
          reportCard(
            'Contribution Report',
            Icons.payments,
            [
              'Records: ${state.contributions.length}',
              'Total: ${money(state.totalContributions)}',
            ],
          ),
          reportCard(
            'Benefit Report',
            Icons.volunteer_activism,
            [
              'Cases: ${state.benefits.length}',
              'Paid: ${money(state.totalBenefits)}',
            ],
          ),
          reportCard(
            'Property Report',
            Icons.business,
            [
              'Properties: ${state.properties.length}',
              'Value: ${money(state.totalPropertyValue)}',
            ],
          ),
        ],
      ),
    );
  }
}

// ============================================================
// MORE MODULES
// ============================================================

class MoreScreen extends StatelessWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final modules = [
      (
        'Benefits & Mutual Support',
        'Community support requests',
        Icons.volunteer_activism,
        const BenefitsScreen()
      ),
      (
        'Community Events',
        'Events and costing',
        Icons.event,
        const EventsScreen()
      ),
      (
        'Property Management',
        'Community assets',
        Icons.business,
        const PropertyScreen()
      ),
      (
        'Fund Sustainability',
        'Fund monitoring',
        Icons.account_balance,
        const FundScreen()
      ),
      (
        'Statistical Models',
        'Analytical indicators',
        Icons.query_stats,
        const StatisticalScreen()
      ),
      (
        'Financial Transactions',
        'Financial records',
        Icons.receipt_long,
        const TransactionsScreen()
      ),
      (
        'Reports & Analytics',
        'Management reports',
        Icons.analytics,
        const ReportsScreen()
      ),
      (
        'Audit Trail',
        'System activity records',
        Icons.fact_check,
        const AuditScreen()
      ),
      (
        'Manuals',
        'Operational guidance',
        Icons.menu_book,
        const ManualsScreen()
      ),
      (
        'User Administration',
        'Roles and access',
        Icons.admin_panel_settings,
        const UsersScreen()
      ),
    ];

    return Scaffold(
      appBar: appBar(
        'More',
        subtitle: 'Iddir system modules',
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(
          vertical: 8,
        ),
        children: [
          ...modules.map(
            (x) => Card(
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor:
                      const Color(0xFFE6EEF6),
                  child: Icon(
                    x.$3,
                    color:
                        const Color(0xFF163A5F),
                  ),
                ),
                title: Text(
                  x.$1,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                subtitle: Text(x.$2),
                trailing: const Icon(
                  Icons.chevron_right,
                ),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => x.$4,
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// AUDIT
// ============================================================

class AuditScreen extends StatelessWidget {
  const AuditScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar(
        'Audit Trail',
        subtitle:
            'Traceable system activities',
      ),
      body: ListView(
        children: const [
          Card(
            child: ListTile(
              leading: Icon(Icons.login),
              title: Text('Successful login'),
              subtitle: Text(
                'admin • Portal',
              ),
            ),
          ),
          Card(
            child: ListTile(
              leading: Icon(Icons.info_outline),
              title: Text('Mobile prototype'),
              subtitle: Text(
                'Activity logging will be connected '
                'to the production backend.',
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// MANUALS
// ============================================================

class ManualsScreen extends StatelessWidget {
  const ManualsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final manuals = [
      (
        'Iddir Operating Manual',
        'Register branches, groups and members; establish '
            'contribution rules; record payments; manage '
            'support requests; administer community events; '
            'maintain property records and reconcile financial '
            'transactions.'
      ),
      (
        'Community Support Management',
        'Support requests should document the event, '
            'beneficiary, approval status, approved amount, '
            'paid amount and reference.'
      ),
      (
        'Property Management',
        'Community property can be registered with acquisition '
            'cost, current value, quantity, condition, ownership '
            'and responsible information.'
      ),
      (
        'Statistical Management',
        'The mobile system demonstrates contribution, '
            'consistency, trust and membership indicators '
            'as measurable variables.'
      ),
      (
        'Audit and Financial Controls',
        'Important activities should be recorded in an audit '
            'trail and transaction references maintained for '
            'accountability.'
      ),
    ];

    return Scaffold(
      appBar: appBar(
        'Manuals',
        subtitle:
            'Operational guidance',
      ),
      body: ListView(
        padding: const EdgeInsets.all(10),
        children: manuals.map((m) {
          return Card(
            child: ExpansionTile(
              leading: const Icon(
                Icons.menu_book,
                color: Color(0xFF163A5F),
              ),
              title: Text(
                m.$1,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                ),
              ),
              childrenPadding:
                  const EdgeInsets.fromLTRB(
                16,
                0,
                16,
                16,
              ),
              children: [
                Text(m.$2),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ============================================================
// USERS
// ============================================================

class UsersScreen extends StatelessWidget {
  const UsersScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar(
        'User Administration',
        subtitle:
            'Role-based access management',
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Card(
            child: ListTile(
              leading: const CircleAvatar(
                child: Icon(
                  Icons.admin_panel_settings,
                ),
              ),
              title: const Text(
                'admin',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                ),
              ),
              subtitle: const Text(
                'Iddir Administrator\n'
                'Module: Portal',
              ),
              isThreeLine: true,
              trailing: statusChip('Active'),
            ),
          ),
          Card(
            child: ListTile(
              leading: const Icon(
                Icons.security,
                color: Color(0xFF163A5F),
              ),
              title: const Text(
                'Role-based access',
              ),
              subtitle: const Text(
                'Administrator\n'
                'Branch Manager\n'
                'Finance Officer\n'
                'Member',
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// EMPTY STATE
// ============================================================

class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(35),
        child: Column(
          mainAxisAlignment:
              MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 65,
              color: Colors.blueGrey,
            ),
            const SizedBox(height: 14),
            Text(
              title,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 19,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.blueGrey,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================
// UI HELPERS
// ============================================================

Widget metricCard(
  String title,
  String value,
  IconData icon,
) {
  return Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                color: const Color(0xFF163A5F),
                size: 22,
              ),
              const Spacer(),
            ],
          ),
          const Spacer(),
          Text(
            title,
            style: const TextStyle(
              fontSize: 12,
              color: Colors.blueGrey,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
              color: Color(0xFF163A5F),
            ),
          ),
        ],
      ),
    ),
  );
}

Widget sectionTitle(String text) {
  return Padding(
    padding: const EdgeInsets.fromLTRB(
      14,
      14,
      14,
      6,
    ),
    child: Text(
      text,
      style: const TextStyle(
        fontWeight: FontWeight.bold,
        fontSize: 17,
        color: Color(0xFF163A5F),
      ),
    ),
  );
}

Widget summaryRow(
  String title,
  String value,
  IconData icon,
  Color color,
) {
  return Row(
    children: [
      CircleAvatar(
        radius: 20,
        backgroundColor: color.withOpacity(.10),
        child: Icon(
          icon,
          color: color,
          size: 20,
        ),
      ),
      const SizedBox(width: 12),
      Expanded(
        child: Text(
          title,
          style: const TextStyle(
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
      Text(
        value,
        style: const TextStyle(
          fontWeight: FontWeight.bold,
        ),
      ),
    ],
  );
}

Widget quickAction(
  BuildContext context,
  String title,
  IconData icon,
  Widget screen,
) {
  return InkWell(
    onTap: () {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => screen,
        ),
      );
    },
    borderRadius: BorderRadius.circular(14),
    child: Card(
      child: Column(
        mainAxisAlignment:
            MainAxisAlignment.center,
        children: [
          Icon(
            icon,
            color: const Color(0xFF163A5F),
            size: 28,
          ),
          const SizedBox(height: 6),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    ),
  );
}

Widget moduleTile(
  BuildContext context,
  String title,
  String subtitle,
  IconData icon,
  Widget screen,
) {
  return ListTile(
    leading: CircleAvatar(
      backgroundColor:
          const Color(0xFFE6EEF6),
      child: Icon(
        icon,
        color: const Color(0xFF163A5F),
      ),
    ),
    title: Text(
      title,
      style: const TextStyle(
        fontWeight: FontWeight.bold,
      ),
    ),
    subtitle: Text(subtitle),
    trailing:
        const Icon(Icons.chevron_right),
    onTap: () {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => screen,
        ),
      );
    },
  );
}

Widget reportCard(
  String title,
  IconData icon,
  List<String> lines,
) {
  return Card(
    child: ExpansionTile(
      leading: Icon(
        icon,
        color: const Color(0xFF163A5F),
      ),
      title: Text(
        title,
        style: const TextStyle(
          fontWeight: FontWeight.bold,
        ),
      ),
      children: lines
          .map(
            (x) => ListTile(
              dense: true,
              title: Text(x),
            ),
          )
          .toList(),
    ),
  );
}

Widget statusChip(String status) {
  Color color;

  switch (status) {
    case 'Paid':
    case 'Active':
    case 'Approved':
    case 'Completed':
      color = Colors.green;
      break;

    case 'Rejected':
    case 'Cancelled':
    case 'Inactive':
      color = Colors.red;
      break;

    case 'Requested':
    case 'Reviewed':
    case 'Planned':
      color = Colors.orange;
      break;

    default:
      color = Colors.blue;
  }

  return Container(
    padding: const EdgeInsets.symmetric(
      horizontal: 9,
      vertical: 5,
    ),
    decoration: BoxDecoration(
      color: color.withOpacity(.10),
      borderRadius: BorderRadius.circular(20),
    ),
    child: Text(
      status,
      style: TextStyle(
        color: color,
        fontWeight: FontWeight.bold,
        fontSize: 11,
      ),
    ),
  );
}

Widget metricRow(
  String label,
  String value,
) {
  return Card(
    child: Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: 16,
        vertical: 13,
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: Colors.blueGrey,
              ),
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              color: Color(0xFF163A5F),
            ),
          ),
        ],
      ),
    ),
  );
}

Widget textField(
  TextEditingController controller,
  String label, {
  TextInputType? keyboard,
  int maxLines = 1,
}) {
  return Padding(
    padding: const EdgeInsets.only(
      bottom: 12,
    ),
    child: TextField(
      controller: controller,
      keyboardType: keyboard,
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        filled: true,
        fillColor: Colors.white,
      ),
    ),
  );
}

Widget dropdown(
  String label,
  String value,
  List<String> values,
  ValueChanged<String> onChanged,
) {
  if (values.isEmpty) {
    return const SizedBox.shrink();
  }

  final safeValue =
      values.contains(value)
          ? value
          : values.first;

  return Padding(
    padding: const EdgeInsets.only(
      bottom: 12,
    ),
    child: DropdownButtonFormField<String>(
      initialValue: safeValue,
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        filled: true,
        fillColor: Colors.white,
      ),
      items: values
          .map(
            (x) => DropdownMenuItem(
              value: x,
              child: Text(
                x,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          )
          .toList(),
      onChanged: (v) {
        if (v != null) {
          onChanged(v);
        }
      },
    ),
  );
}

// ============================================================
// UTILITIES
// ============================================================

String money(double value) {
  return '${value.toStringAsFixed(2)} ETB';
}

String today() {
  final d = DateTime.now();

  return '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';
}
