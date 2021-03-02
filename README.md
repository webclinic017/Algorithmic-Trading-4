# AlgoTrading
 Jim Simons wannabe loses money
 
| Simulate![VideoBlocks](History/examplesimulation.JPG?raw=true) | Signal![VideoBlocks](History/examplesignal.JPG?raw=true) |
|:---:|:---:|

Contents:\
[1 Overview](#1-overview)\
[1.1 Goals](#11-goals)\
[1.2 Requirements](#12-requirements)\
[1.3 Edge](#13-edge)\
\
[2 Technical Analysis](#2-platform)\
[2.1 Goals](#21-goals)\
[2.2 Requirements](#22-requirements)\
[2.3 Progress](#23-progress)\
\
[3 Sentiment Analysis](#3-sentiment-analysis)\
[3.1 Goals](#31-goals)\
[3.2 Requirements](#32-requirements)\
[3.3 Progress](#33-progress)
 

## 1 Overview
This readme briefly captures thoughts.

### 1.1 Goals
*What will it do?*
1. Extra income with minimal supervision
2. Learn something and enjoy
3. Make this repository private 

### 1.2 Requirements
*How will it get done?*
1. Data management
2. Backtest
4. Paper trade
5. Risk Management
6. Automation
7. Auditing/transaction logging

### 1.3 Edge
*Why will it get done?*\
Trade medium frequency/low capacity strategies.\
Can't beat the hediges. 


## 2. Platform
Run the strategies throughout the day. Provide entry, exits and manage risk.
Ideally have a reliable core portfolio, and riskier satellite. Current ideas - \
a) Trade ETFs capturing swings with well established technical indicators. Beat the index long term & avoid big downdraw \
b) Long volatility plays on low market-cap which are hyped (capture pump and dumps). Volume and online sentiment as potential indicators. 


### 2.1 Goals
1. Backtest
2. Paper trade
3. Optimise -- check parameter sweep for win/loss correlation
4. Be as close in code and operation to real trading, so the transition is easier

### 2.2 Requirements
1. Meticulous data storage
0.1 Automatically scrape, repair and clean data- get early get often
2. Multiple strategies, interfacing to broker and account
3. Manage risk and sizing
4.1 Set aim for enter, exit and stop
5.2 Reallocate max with Sharpe-ratio
6. Book keeping
7. Aim for autonomy, but potential for remote decision making notifications

### 2.3 Progress
- [x] Data management 
- [x] Basic Strategies
- [x] Basic optimisation
- [x] Automation via email signal notifications
- [ ] Better strategies...
- [ ] Window optimsation (overfitting?)


## 3. Sentiment Analysis
Scrape the sentiment of online-traders. 
Use to inform the trading platform.
While this probably won't give good tips, can be to supplement other strategies though.

### 3.1 Goals
1. Have an indicator for upcoming volume and opportunity
2. Daily reporting
3. Individual tickers and general market trends

### 3.2 Requirements
1. Avoid look-ahead bias, so don't pull any historical (start collecting asap). Many more mentions directly after a pump.
2. How to determine sentiment? 
3. How to discern bad actors?

### 3.3 Progress
- [x] Very basic scraping and collection schedule.

