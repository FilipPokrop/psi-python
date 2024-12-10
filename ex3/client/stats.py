from math import sqrt


class Statistics:
    def __init__(self):
        self.tsum = 0.0
        self.tsumsq = 0.0
        self.tmin = float("inf")
        self.tmax = float("-inf")
        self.psend = 0
        self.precive = 0

    def __str__(self):
        return f"{self.packets_str()}\n{self.rrt_str()}"
        pass

    def send(self):
        self.psend += 1

    def recive(self, triptime):
        self.precive += 1
        self.tsum += triptime
        self.tsumsq += triptime**2
        self.tmin = min(self.tmin, triptime)
        self.tmax = max(self.tmax, triptime)

    def packets_str(self):
        lost = (self.psend - self.precive) / self.psend
        return (
            f"{self.psend} packet transmitted, "
            + f"{self.precive} recived, "
            + f"lost {lost:%}"
        )

    def rrt_str(self):
        if self.precive == 0:
            return ""
        avg = self.tsum / self.precive
        std = sqrt(self.tsumsq / self.precive - avg**2)
        return "rrt min/avg/max/std = " + f"{self.tmin:.3f}/{avg:.3f}/{self.tmax:.3f}/{std:.3f}"


if __name__ == "__main__":
    s = Statistics()
    s.send()
    s.recive(1)
    s.send()
    s.recive(2)
    print(s)
