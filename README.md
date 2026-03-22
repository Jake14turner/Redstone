If you would like to try for yourself, simply run this python file: python main.py

# Redstone Logic — How to Save a Value to RAM

## What You're Looking At

Your RAM circuit has three main sections:

- **Decoder (left column)** — takes your address bits as input and activates exactly one row
- **Address lines (horizontal wires)** — carry the row-select signal across to the memory cells
- **SR Latch stacks (the tower structures)** — each one is a column of memory cells, one per row

Each intersection of a row-select line and an SR latch is one bit of storage.

---

## Step 1 — Choose Your Address

The decoder on the left reads your select bits. If you have 8 rows, you need 3 select bits (2³ = 8). Turn on the power sources that represent the binary address of the row you want to write to.

**Example — selecting row 5 (binary `101`):**

| Bit 2 | Bit 1 | Bit 0 |
|-------|-------|-------|
| ON    | OFF   | ON    |

The decoder will activate **only that row's** horizontal line. All other rows remain isolated.

---

## Step 2 — Set Your Data Bits

Each SR latch column represents one bit of your data.

- To write a **`1`** to a bit → pulse the **Set (S)** input of that latch
- To write a **`0`** to a bit → pulse the **Reset (R)** input of that latch

Your data inputs are the wires feeding into the S and R sides of each latch stack. Set these **before** you enable the write clock.

---

## Step 3 — Enable the Write Clock

The clock gate controls whether the row-select signal actually reaches the latches.

- Clock **OFF** → the row is isolated, no writes can happen even if the address is selected
- Clock **ON** → the selected row's signal passes through to the latch inputs

**Pulse the clock ON then OFF.** This is your write strobe. The latch holds the value after the clock goes low — that's the whole point of an SR latch, it remembers.

### Write sequence in order:
1. Set your address bits
2. Set your data bits (S or R inputs)
3. Pulse the clock ON
4. Pulse the clock OFF
5. Value is now stored

---

## Step 4 — Reading Back

To read a stored value:

1. Set the same address bits as when you wrote
2. Keep the **write clock OFF**
3. The output lines of the latches for that row reflect the stored value:
   - Powered → `1`
   - Unpowered → `0`

Because the clock is off, you're just observing the latch outputs — you're not writing anything.

---

## Key Rules

> **Never change the address while the write clock is high.**
> If the address changes mid-clock, you'll accidentally write to multiple rows simultaneously. Always: set address → then pulse clock.

> **Always pulse, never hold.**
> Holding the clock high leaves the row open to writes. A brief pulse is enough to latch the value.

> **S and R should never both be ON at the same time.**
> This is an illegal state for an SR latch and produces undefined behavior. Make sure only one is active when you write.

---

## Quick Reference

| Action | Address | S/R Inputs | Clock |
|--------|---------|------------|-------|
| Write a 1 | Set target row | S = ON, R = OFF | Pulse |
| Write a 0 | Set target row | S = OFF, R = ON | Pulse |
| Read | Set target row | Don't care | OFF |
| Idle | Any | Don't care | OFF |