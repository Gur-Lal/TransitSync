# TransitSync

**A smarter way to think about connections between Montréal's Metro and REM.**

When we miss a connection, it can add a lot of time to our trip. If we decide holding a Metro train for arriving passengers, it would also delay everyone already on board and can affect the trains behind it. Our capstone project explores how to make that tradeoff more thoughtfully.

TransitSync is a **simulation and decision-support prototype** for coordinating transfers between the STM Metro and the REM. It tests whether a short train hold could help more passengers than it delays. The aim is to give transit planners a way to compare possible strategies and choose the best one in different situations.

## What we're building

- A simulation of passenger transfers and train movement, starting with Metro–REM connections.
- A controller that considers arriving passengers, passengers already on board, and the effect of a delay farther along the line.
- A maximum hold time.
- A comparison of trips with and without the controller, using different measures such as missed connections, passenger waiting time, and total passenger delay.
- A way to visualize decisions and results so we can explain *why or why not* the controller chose to hold or release a train.

We plan to begin with Metro–REM transfers, then explore transfers between Metro lines i time allows us to do so.

## A simple example

Suppose a REM train is arriving and several passengers are about to transfer to the Metro. Should the Metro wait few seconds extra so the passengers coming can make it and not wait an at least extra 5 minutes? TransitSync estimates how much time those passengers might save and weighs that against the delay to people on the Metro and people waiting farther down the line. Sometimes waiting will make sense; sometimes letting the train leave will be better for the network as a whole.

## Project status

This is a 1 year software engineering capstone project at Concordia University, built by The Exception Handlers team.

## Getting started

Setup instructions will be added when the first runnable version is available.

## Team

Built by The Exception Handlers, a Concordia University software engineering capstone team.
