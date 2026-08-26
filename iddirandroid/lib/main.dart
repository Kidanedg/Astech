import 'package:flutter/material.dart';

void main() => runApp(const IddirApp());

class IddirApp extends StatefulWidget {
  const IddirApp({super.key});
  @override
  State<IddirApp> createState() => _IddirAppState();
}

class _IddirAppState extends State<IddirApp> {
  bool loggedIn = false;
  int index = 0;
  String user = 'Administrator';

  final List<Map<String, dynamic>> members = [
    {'id': 'M001', 'name': 'Tesfay Abraha', 'phone': '0911000001', 'group': 'St. Mary', 'status': 'Active', 'contribution': 200},
    {'id': 'M002', 'name': 'Hana Gebre', 'phone': '0911000002', 'group': 'St. Mary', 'status': 'Active', 'contribution': 200},
    {'id': 'M003', 'name': 'Desta Kahsay', 'phone': '0911000003', 'group': 'St. Michael', 'status': 'Active', 'contribution': 250},
  ];

  final List<Map<String, dynamic>> groups = [
    {'name': 'St. Mary', 'members': 42, 'monthly': 200, 'fund': 8400.0},
    {'name': 'St. Michael', 'members': 31, 'monthly': 250, 'fund': 7750.0},
    {'name': 'St. George', 'members': 27, 'monthly': 200, 'fund': 5400.0},
  ];

  final List<Map<String, dynamic>> transactions = [
    {'date': '2026-08-20', 'type': 'Contribution', 'ref': 'TX-1001', 'amount': 200.0, 'member': 'Tesfay Abraha'},
    {'date': '2026-08-19', 'type': 'Benefit', 'ref': 'TX-1000', 'amount': -1500.0, 'member': 'Hana Gebre'},
    {'date': '2026-08-18', 'type': 'Contribution', 'ref': 'TX-0999', 'amount': 250.0, 'member': 'Desta Kahsay'},
  ];

  final List<Map<String, dynamic>> audit = [];

  final moduleNames = const [
    'Dashboard',
    'Branch Management',
    'Member Management',
    'Iddir Groups',
    'Contributions',
    'Benefits & Mutual Support',
    'Community Events',
    'Property Management',
    'Property Analytics',
    'Fund Sustainability',
    'Statistical Models',
    'Financial Transactions',
    'Reports & Analytics',
    'Manuals',
    'Audit Trail',
    'User Administration',
  ];

  void log(String action) {
    audit.insert(0, {
      'time': DateTime.now().toString().substring(0, 19),
      'user': user,
      'action': action,
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'IDFS Iddir',
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.indigo,
        scaffoldBackgroundColor: const Color(0xfff5f7fb),
      ),
      home: loggedIn
          ? _shell()
          : LoginPage(onLogin: (u) => setState(() {
                user = u;
                loggedIn = true;
                log('User logged in');
              })),
    );
  }

  Widget _shell() {
    return LayoutBuilder(builder: (context, c) {
      final wide = c.maxWidth >= 900;
      return Scaffold(
        appBar: AppBar(
          title: Text('IDFS Iddir • ${moduleNames[index]}'),
          actions: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Center(child: Text(user)),
            ),
            IconButton(
              tooltip: 'Logout',
              onPressed: () => setState(() {
                log('User logged out');
                loggedIn = false;
              }),
              icon: const Icon(Icons.logout),
            )
          ],
        ),
        drawer: wide ? null : Drawer(child: _navigation()),
        body: Row(
          children: [
            if (wide) SizedBox(width: 285, child: _navigation()),
            Expanded(child: _page()),
          ],
        ),
      );
    });
  }

  Widget _navigation() {
    return Material(
      color: Colors.white,
      child: SafeArea(
        child: ListView(
          padding: const EdgeInsets.symmetric(vertical: 12),
          children: [
            const Padding(
              padding: EdgeInsets.all(20),
              child: Text('IDFS IDDIR',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.dashboard),
              title: const Text('Dashboard'),
              selected: index == 0,
              onTap: () => _select(0),
            ),
            for (int i = 1; i < moduleNames.length; i++)
              ListTile(
                dense: true,
                leading: Icon(_icon(i)),
                title: Text(moduleNames[i]),
                selected: index == i,
                onTap: () => _select(i),
              ),
          ],
        ),
      ),
    );
  }

  IconData _icon(int i) {
    const icons = [
      Icons.account_tree, Icons.people, Icons.groups, Icons.payments,
      Icons.volunteer_activism, Icons.event, Icons.home_work, Icons.analytics,
      Icons.savings, Icons.auto_graph, Icons.receipt_long, Icons.assessment,
      Icons.menu_book, Icons.security, Icons.admin_panel_settings
    ];
    return icons[i - 1];
  }

  void _select(int i) {
    setState(() => index = i);
    if (Navigator.canPop(context)) Navigator.pop(context);
  }

  Widget _page() {
    switch (index) {
      case 0: return DashboardPage(members: members, groups: groups, transactions: transactions, onAdd: _showTransaction);
      case 1: return BranchPage(onChanged: log);
      case 2: return MemberPage(members: members, groups: groups, onChanged: log);
      case 3: return GroupPage(groups: groups, onChanged: log);
      case 4: return ContributionPage(members: members, transactions: transactions, onChanged: log);
      case 5: return BenefitPage(onChanged: log);
      case 6: return EventPage(onChanged: log);
      case 7: return PropertyPage(onChanged: log);
      case 8: return PropertyAnalyticsPage();
      case 9: return SustainabilityPage(groups: groups);
      case 10: return StatisticalModelsPage();
      case 11: return TransactionPage(transactions: transactions, onAdd: _showTransaction, onChanged: log);
      case 12: return ReportsPage(members: members, groups: groups, transactions: transactions);
      case 13: return ManualsPage();
      case 14: return AuditPage(audit: audit);
      case 15: return UserAdminPage(onChanged: log);
      default: return const SizedBox();
    }
  }

  void _showTransaction() {
    final amount = TextEditingController();
    final member = TextEditingController();
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('New Financial Transaction'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: member, decoration: const InputDecoration(labelText: 'Member')),
          TextField(controller: amount, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Amount (ETB)')),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              transactions.insert(0, {
                'date': DateTime.now().toString().substring(0, 10),
                'type': 'Contribution',
                'ref': 'TX-${1000 + transactions.length + 1}',
                'amount': double.tryParse(amount.text) ?? 0,
                'member': member.text.isEmpty ? 'Unknown' : member.text,
              });
              log('Created financial transaction');
              setState(() {});
              Navigator.pop(context);
            },
            child: const Text('Save'),
          )
        ],
      ),
    );
  }
}

class LoginPage extends StatefulWidget {
  final void Function(String) onLogin;
  const LoginPage({super.key, required this.onLogin});
  @override State<LoginPage> createState() => _LoginPageState();
}
class _LoginPageState extends State<LoginPage> {
  final u = TextEditingController(text: 'admin');
  final p = TextEditingController(text: 'admin');
  @override Widget build(BuildContext context) => Scaffold(
    body: Center(child: Card(
      child: SizedBox(width: 380, child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.account_balance, size: 60),
          const SizedBox(height: 12),
          const Text('IDFS IDDIR', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
          const Text('Indigenous Digital Financial System'),
          const SizedBox(height: 24),
          TextField(controller: u, decoration: const InputDecoration(labelText: 'Username')),
          TextField(controller: p, obscureText: true, decoration: const InputDecoration(labelText: 'Password')),
          const SizedBox(height: 20),
          SizedBox(width: double.infinity, child: FilledButton(
            onPressed: () => widget.onLogin(u.text.isEmpty ? 'Administrator' : u.text),
            child: const Text('LOGIN'),
          ))
        ]),
      ),
    )),
  );
}

class DashboardPage extends StatelessWidget {
  final List<Map<String, dynamic>> members;
  final List<Map<String, dynamic>> groups;
  final List<Map<String, dynamic>> transactions;
  final VoidCallback onAdd;

  const DashboardPage({
    super.key,
    required this.members,
    required this.groups,
    required this.transactions,
    required this.onAdd,
  });

  @override
  Widget build(BuildContext context) {
    final fund = groups.fold<double>(
      0,
      (sum, group) => sum + (group['fund'] as num).toDouble(),
    );

    return PageScaffold(
      title: 'Dashboard',
      actions: [
        FilledButton.icon(
          onPressed: onAdd,
          icon: const Icon(Icons.add),
          label: const Text('Transaction'),
        ),
      ],
      children: [
        const Text(
          'Community overview and operational status.',
          style: TextStyle(color: Colors.grey),
        ),
        const SizedBox(height: 18),

        GridView.count(
          crossAxisCount:
              MediaQuery.sizeOf(context).width > 1000 ? 4 : 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: 1.7,
          children: [
            StatCard(
              'Members',
              '${members.length}',
              Icons.people,
            ),
            StatCard(
              'Iddir Groups',
              '${groups.length}',
              Icons.groups,
            ),
            StatCard(
              'Community Fund',
              'ETB ${fund.toStringAsFixed(0)}',
              Icons.savings,
            ),
            StatCard(
              'Transactions',
              '${transactions.length}',
              Icons.receipt_long,
            ),
          ],
        ),

        const SizedBox(height: 20),

        SectionCard(
          title: 'Recent Transactions',
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: const [
                DataColumn(label: Text('Date')),
                DataColumn(label: Text('Type')),
                DataColumn(label: Text('Member')),
                DataColumn(label: Text('Amount')),
              ],
              rows: transactions.take(8).map((transaction) {
                return DataRow(
                  cells: [
                    DataCell(Text('${transaction['date']}')),
                    DataCell(Text('${transaction['type']}')),
                    DataCell(Text('${transaction['member']}')),
                    DataCell(
                      Text('ETB ${transaction['amount']}'),
                    ),
                  ],
                );
              }).toList(),
            ),
          ),
        ),
      ],
    );
  }
}

class BranchPage extends StatelessWidget {
  final void Function(String) onChanged;
  const BranchPage({super.key, required this.onChanged});
  @override Widget build(BuildContext context) => CrudPage(title:'Branch Management', icon:Icons.account_tree, columns:['Code','Branch','Manager','Status'], rows:[
    ['BR-001','Aksum Central','Administrator','Active'],
    ['BR-002','Mai Aini','Branch Officer','Active'],
    ['BR-003','Adwa','Branch Officer','Active'],
  ], onChanged:onChanged);
}

class MemberPage extends StatefulWidget {
  final List<Map<String,dynamic>> members, groups;
  final void Function(String) onChanged;
  const MemberPage({super.key, required this.members, required this.groups, required this.onChanged});
  @override State<MemberPage> createState()=>_MemberPageState();
}
class _MemberPageState extends State<MemberPage> {
  void add() {
    final name = TextEditingController();
    final phone = TextEditingController();
    final contribution = TextEditingController(text: '200');

    String group = widget.groups.first['name'];

    showDialog(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (c, setD) => AlertDialog(
          title: const Text('Register Member'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: name,
                  decoration: const InputDecoration(
                    labelText: 'Full name',
                  ),
                ),
                TextField(
                  controller: phone,
                  decoration: const InputDecoration(
                    labelText: 'Phone',
                  ),
                ),
                DropdownButtonFormField<String>(
                  initialValue: group,
                  items: widget.groups
                      .map(
                        (g) => DropdownMenuItem<String>(
                          value: g['name'] as String,
                          child: Text(g['name']),
                        ),
                      )
                      .toList(),
                  onChanged: (v) {
                    if (v != null) {
                      setD(() {
                        group = v;
                      });
                    }
                  },
                  decoration: const InputDecoration(
                    labelText: 'Iddir group',
                  ),
                ),
                TextField(
                  controller: contribution,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Monthly / round contribution (ETB)',
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(c),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                widget.members.add({
                  'id': 'M${100 + widget.members.length}',
                  'name': name.text,
                  'phone': phone.text,
                  'group': group,
                  'status': 'Active',
                  'contribution':
                      double.tryParse(contribution.text) ?? 0,
                });

                widget.onChanged(
                  'Registered member ${name.text}',
                );

                setState(() {});
                Navigator.pop(c);
              },
              child: const Text('Register'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PageScaffold(
      title: 'Member Management',
      actions: [
        FilledButton.icon(
          onPressed: add,
          icon: const Icon(Icons.person_add),
          label: const Text('Register Member'),
        ),
      ],
      children: [
        SectionCard(
          title: 'Members',
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: const [
                DataColumn(label: Text('ID')),
                DataColumn(label: Text('Name')),
                DataColumn(label: Text('Phone')),
                DataColumn(label: Text('Group')),
                DataColumn(label: Text('Contribution')),
                DataColumn(label: Text('Status')),
              ],
              rows: widget.members
                  .map(
                    (m) => DataRow(
                      cells: [
                        DataCell(Text('${m['id']}')),
                        DataCell(Text('${m['name']}')),
                        DataCell(Text('${m['phone']}')),
                        DataCell(Text('${m['group']}')),
                        DataCell(
                          Text('ETB ${m['contribution']}'),
                        ),
                        DataCell(Text('${m['status']}')),
                      ],
                    ),
                  )
                  .toList(),
            ),
          ),
        ),
      ],
    );
  }
}

class GroupPage extends StatelessWidget {
  final List<Map<String,dynamic>> groups;
  final void Function(String) onChanged;
  const GroupPage({super.key,required this.groups,required this.onChanged});
  @override Widget build(BuildContext context)=>CrudPage(title:'Iddir Groups',icon:Icons.groups,columns:['Group','Members','Contribution','Fund'],rows:groups.map((g)=>['${g['name']}','${g['members']}','ETB ${g['monthly']}','ETB ${g['fund']}']).toList(),onChanged:onChanged);
}

class ContributionPage extends StatelessWidget {
  final List<Map<String,dynamic>> members,transactions;
  final void Function(String) onChanged;
  const ContributionPage({super.key,required this.members,required this.transactions,required this.onChanged});
  @override Widget build(BuildContext context)=>PageScaffold(title:'Contributions',actions:[FilledButton(onPressed:()=>_record(context),child:const Text('Record Contribution'))],children:[
    SectionCard(title:'Contribution Schedule',child:DataTable(columns:const[DataColumn(label:Text('Member')),DataColumn(label:Text('Group')),DataColumn(label:Text('Expected')),DataColumn(label:Text('Status'))],rows:members.map((m)=>DataRow(cells:[
      DataCell(Text('${m['name']}')),DataCell(Text('${m['group']}')),DataCell(Text('ETB ${m['contribution']}')),const DataCell(Chip(label:Text('Due')))] )).toList()))
  ]);
  void _record(BuildContext c){showDialog(context:c,builder:(_)=>AlertDialog(title:const Text('Record Contribution'),content:const Text('Select a member and record the amount paid. The transaction module stores the financial entry.'),actions:[TextButton(onPressed:()=>Navigator.pop(c),child:const Text('Close'))]));}
}

class BenefitPage extends StatelessWidget {
  final void Function(String) onChanged;
  const BenefitPage({super.key,required this.onChanged});
  @override Widget build(BuildContext context)=>CrudPage(title:'Benefits & Mutual Support',icon:Icons.volunteer_activism,columns:['Case','Member/Family','Benefit Type','Amount','Status'],rows:[
    ['BS-001','Hana Gebre','Bereavement support','ETB 1,500','Approved'],
    ['BS-002','Community','Emergency support','ETB 2,000','Pending'],
  ],onChanged:onChanged);
}
class EventPage extends StatelessWidget {
  final void Function(String) onChanged;
  const EventPage({super.key,required this.onChanged});
  @override Widget build(BuildContext context)=>CrudPage(title:'Community Events',icon:Icons.event,columns:['Date','Event','Location','Coordinator','Status'],rows:[
    ['2026-09-01','Annual General Meeting','Community Hall','Committee','Planned'],
    ['2026-09-10','Community Cleaning','Main Square','Youth Team','Planned'],
  ],onChanged:onChanged);
}
class PropertyPage extends StatelessWidget {
  final void Function(String) onChanged;
  const PropertyPage({super.key,required this.onChanged});
  @override Widget build(BuildContext context)=>CrudPage(title:'Property Management',icon:Icons.home_work,columns:['Asset ID','Property','Type','Value','Status'],rows:[
    ['P-001','Community Hall','Building','ETB 850,000','Active'],
    ['P-002','Meeting Chairs','Equipment','ETB 85,000','Active'],
    ['P-003','Land Parcel','Land','ETB 400,000','Active'],
  ],onChanged:onChanged);
}
class PropertyAnalyticsPage extends StatelessWidget {
  const PropertyAnalyticsPage({super.key});
  @override Widget build(BuildContext context)=>PageScaffold(title:'Property Analytics',children:[
    const SectionCard(title:'Portfolio Summary',child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text('Total estimated property value: ETB 1,335,000',style:TextStyle(fontSize:22,fontWeight:FontWeight.bold)),
      SizedBox(height:10),Text('Buildings: 63.7%   •   Land: 30.0%   •   Equipment: 6.4%')
    ])),
    const SizedBox(height:16),
    SectionCard(title:'Asset Indicators',child:Column(children:[
      LinearProgressIndicator(value:.82), const SizedBox(height:8), const Text('Asset utilization: 82%'),
      SizedBox(height:18), LinearProgressIndicator(value:.71), const SizedBox(height:8), const Text('Maintenance readiness: 71%'),
    ]))
  ]);
}
class SustainabilityPage extends StatelessWidget {
  final List<Map<String,dynamic>> groups;
  const SustainabilityPage({super.key,required this.groups});
  @override Widget build(BuildContext context)=>PageScaffold(title:'Fund Sustainability',children:[
    SectionCard(title:'Sustainability Indicators',child:Column(children:[
      Indicator('Contribution coverage ratio',.91),
      Indicator('Emergency reserve ratio',.74),
      Indicator('Benefit affordability index',.83),
      Indicator('Fund continuity score',.88),
    ])),
    const SizedBox(height:16), SectionCard(title:'Interpretation',child:Text('The indicators are designed to support committee decisions about reserves, contribution adequacy, benefit commitments, and long-term community financial resilience.'))
  ]);
}
class StatisticalModelsPage extends StatelessWidget {
  const StatisticalModelsPage({super.key});
  @override Widget build(BuildContext context)=>PageScaffold(title:'Statistical Models',children:[
    SectionCard(title:'Community Risk Model',child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      const Text('Purpose: identify emerging contribution, benefit, liquidity, and participation risks.'),
      const SizedBox(height:12),
      const Text('Risk Score = w₁C + w₂B + w₃L + w₄P'),
      const SizedBox(height:12),
      Indicator('Contribution consistency',.86),
      Indicator('Benefit pressure',.32),
      Indicator('Liquidity risk',.24),
      Indicator('Participation stability',.91),
    ])),
    const SizedBox(height:16), const SectionCard(title:'Model Governance',child:Text('Models are decision-support tools. Committee approval remains required for benefits, exceptional payments, property decisions, and policy changes.'))
  ]);
}
class TransactionPage extends StatelessWidget {
  final List<Map<String,dynamic>> transactions; final VoidCallback onAdd; final void Function(String) onChanged;
  const TransactionPage({super.key,required this.transactions,required this.onAdd,required this.onChanged});
  @override Widget build(BuildContext context)=>PageScaffold(title:'Financial Transactions',actions:[FilledButton.icon(onPressed:onAdd,icon:const Icon(Icons.add),label:const Text('New Transaction'))],children:[
    SectionCard(title:'Ledger',child:SingleChildScrollView(scrollDirection:Axis.horizontal,child:DataTable(columns:const[
      DataColumn(label:Text('Date')),DataColumn(label:Text('Reference')),DataColumn(label:Text('Type')),DataColumn(label:Text('Member')),DataColumn(label:Text('Amount'))
    ],rows:transactions.map((x)=>DataRow(cells:[DataCell(Text('${x['date']}')),DataCell(Text('${x['ref']}')),DataCell(Text('${x['type']}')),DataCell(Text('${x['member']}')),DataCell(Text('ETB ${x['amount']}'))])).toList())))
  ]);
}
class ReportsPage extends StatelessWidget {
  final List<Map<String,dynamic>> members,groups,transactions;
  const ReportsPage({super.key,required this.members,required this.groups,required this.transactions});
  @override Widget build(BuildContext context)=>PageScaffold(title:'Reports & Analytics',children:[
    GridView.count(crossAxisCount:MediaQuery.sizeOf(context).width>900?3:1,shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),childAspectRatio:2.4,children:[
      StatCard('Member participation','${members.length} active records',Icons.people),
      StatCard('Group fund','ETB ${groups.fold<double>(0,(s,g)=>s+(g['fund'] as num).toDouble()).toStringAsFixed(0)}',Icons.savings),
      StatCard('Ledger entries','${transactions.length}',Icons.receipt),
    ]),
    const SizedBox(height:18),const SectionCard(title:'Available Reports',child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      ListTile(leading:Icon(Icons.description),title:Text('Monthly contribution report'),subtitle:Text('Expected, collected, arrears and participation.')),
      ListTile(leading:Icon(Icons.description),title:Text('Benefit and mutual support report'),subtitle:Text('Cases, approvals, disbursements and balances.')),
      ListTile(leading:Icon(Icons.description),title:Text('Financial statement'),subtitle:Text('Receipts, payments, balances and transaction history.')),
      ListTile(leading:Icon(Icons.description),title:Text('Property register'),subtitle:Text('Assets, estimated values and utilization.')),
    ]))
  ]);
}
class ManualsPage extends StatelessWidget {
  const ManualsPage({super.key});
  @override Widget build(BuildContext context)=>PageScaffold(title:'Manuals',children:[
    const SectionCard(title:'System Manuals',child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text('1. Administrator Manual',style:TextStyle(fontWeight:FontWeight.bold)),
      Text('User administration, branches, permissions, audit review and system configuration.'),
      SizedBox(height:14),
      Text('2. Treasurer Manual',style:TextStyle(fontWeight:FontWeight.bold)),
      Text('Contributions, benefits, receipts, payments, reconciliation and reports.'),
      SizedBox(height:14),
      Text('3. Committee Manual',style:TextStyle(fontWeight:FontWeight.bold)),
      Text('Group governance, approvals, mutual support, events and community decisions.'),
      SizedBox(height:14),
      Text('4. Member Manual',style:TextStyle(fontWeight:FontWeight.bold)),
      Text('Registration, contribution tracking, benefits, events and account information.'),
    ]))
  ]);
}
class AuditPage extends StatelessWidget {
  final List<Map<String,dynamic>> audit;
  const AuditPage({super.key,required this.audit});
  @override Widget build(BuildContext context)=>PageScaffold(title:'Audit Trail',children:[
    SectionCard(title:'System Activity',child:audit.isEmpty?const Text('No activity recorded in this session.'):DataTable(columns:const[
      DataColumn(label:Text('Time')),DataColumn(label:Text('User')),DataColumn(label:Text('Action'))
    ],rows:audit.map((x)=>DataRow(cells:[DataCell(Text('${x['time']}')),DataCell(Text('${x['user']}')),DataCell(Text('${x['action']}'))])).toList()))
  ]);
}
class UserAdminPage extends StatelessWidget {
  final void Function(String) onChanged;
  const UserAdminPage({super.key,required this.onChanged});
  @override Widget build(BuildContext context)=>CrudPage(title:'User Administration',icon:Icons.admin_panel_settings,columns:['Username','Role','Branch','Status'],rows:[
    ['admin','System Administrator','Head Office','Active'],
    ['treasurer','Treasurer','Aksum Central','Active'],
    ['committee','Committee Officer','Aksum Central','Active'],
  ],onChanged:onChanged);
}

class PageScaffold extends StatelessWidget {
  final String title; final List<Widget> children; final List<Widget>? actions;
  const PageScaffold({super.key,required this.title,required this.children,this.actions});
  @override Widget build(BuildContext context)=>SingleChildScrollView(padding:const EdgeInsets.all(22),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
    Row(children:[Expanded(child:Text(title,style:const TextStyle(fontSize:28,fontWeight:FontWeight.bold))),...(actions??[]) ]),const SizedBox(height:6),...children
  ]));
}
class SectionCard extends StatelessWidget {
  final String title; final Widget child;
  const SectionCard({super.key,required this.title,required this.child});
  @override Widget build(BuildContext context)=>Card(child:Padding(padding:const EdgeInsets.all(18),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
    Text(title,style:const TextStyle(fontSize:18,fontWeight:FontWeight.bold)),const SizedBox(height:12),child
  ])));
}
class StatCard extends StatelessWidget {
  final String title,value; final IconData icon;
  const StatCard(this.title,this.value,this.icon,{super.key});
  @override Widget build(BuildContext context)=>Card(child:Padding(padding:const EdgeInsets.all(16),child:Row(children:[
    Icon(icon,size:38),const SizedBox(width:14),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,mainAxisAlignment:MainAxisAlignment.center,children:[
      Text(title,style:const TextStyle(color:Colors.grey)),Text(value,style:const TextStyle(fontSize:21,fontWeight:FontWeight.bold))
    ]))
  ])));
}
class Indicator extends StatelessWidget {
  final String label; final double value;
  const Indicator(this.label,this.value,{super.key});
  @override Widget build(BuildContext context)=>Padding(padding:const EdgeInsets.only(bottom:16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
    Row(children:[Expanded(child:Text(label)),Text('${(value*100).toStringAsFixed(0)}%')]),
    const SizedBox(height:5),LinearProgressIndicator(value:value)
  ]));
}
class CrudPage extends StatelessWidget {
  final String title; final IconData icon; final List<String> columns; final List<List<String>> rows; final void Function(String) onChanged;
  const CrudPage({super.key,required this.title,required this.icon,required this.columns,required this.rows,required this.onChanged});
  @override Widget build(BuildContext context)=>PageScaffold(title:title,actions:[FilledButton.icon(onPressed:()=>onChanged('Opened create form in $title'),icon:const Icon(Icons.add),label:const Text('Add'))],children:[
    SectionCard(title:'Records',child:SingleChildScrollView(scrollDirection:Axis.horizontal,child:DataTable(
      columns:columns.map((x)=>DataColumn(label:Text(x))).toList(),
      rows:rows.map((r)=>DataRow(cells:r.map((x)=>DataCell(Text(x))).toList())).toList(),
    )))
  ]);
}
