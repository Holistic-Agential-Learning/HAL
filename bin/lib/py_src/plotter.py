import threading
import matplotlib.pyplot as plt
import pickle
import zmq

class Plotter:

    def __init__(self, file_name, maxtwo, min_frames, max_frames):
        self.fname = file_name
        frame_rate = 10000.0 if maxtwo else 20000.0
        self.upper = frame_rate / min_frames + 0.5
        self.lower = frame_rate / max_frames - 0.5

        self.plot_lock = threading.Lock()
        self.data_cond = threading.Condition(self.plot_lock)
        self.plot_data = []
    
    def _sync(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:5556")
        try:
            message = socket.recv()
        except KeyboardInterrupt:
            return

        # Send message back to closed-loop program
        socket.send(b"sync")

    def _plot_producer(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5555")
        socket.setsockopt(zmq.SUBSCRIBE, b"")

        self._sync()

        done = False

        while not done:

            try:
                # print("waiting for message")
                message = socket.recv()
            except KeyboardInterrupt:
                print("producer detected interrupt!")
                break

            with self.data_cond:
                if (message == b"stop"):
                    self.plot_data.append("stop")
                    print("stop detected!")
                    done = True
                    
                else:
                    b,t,s,r = message.decode("utf-8").split(";")

                    self.plot_data.append([b, t, s, r])

                self.data_cond.notify()

    def plot_frequency_game(self):
        producer = threading.Thread(target=self._plot_producer, args=[])

        producer.start()

        buttons = ["A", "B"]
        bar_colors = ["red", "blue"]
        button_counts = [0, 0]
        times = []
        stim_levels = []
        frequencies = []

        fig = plt.gcf()
        fig.show()

        freqpath = plt.subplot(311)
        freqpath.set_title("Stimulation Frequency")
        freqpath.set_ylabel("Stimulations per Second")
        freqpath.set_xlabel("Time (s)")
        freqpath.set_ylim(self.lower, self.upper)

        space = plt.subplot(312)
        space.set_title("Frequency World")
        space.set_ylabel("Stimulation Level")
        space.set_xlabel("Time")
        space.set_ylim(-1, 11)

        count = plt.subplot(313)
        count.set_title("Total Button Presses")
        count.set_ylabel("Count")
        count.set_xlabel("Buttons")

        fig.tight_layout()
        fig.canvas.draw()

        print("plot initialized")

        done = False
        try:
            while not done:

                with self.data_cond:
                    while len(self.plot_data) == 0:
                        self.data_cond.wait()

                    for item in self.plot_data:
                        if (item == "stop"):
                            done = True
                            print("plotter: stop detected")
                        else:
                            b, t, s, r = item
                            if (b == "A"):
                                button_counts[0] = button_counts[0] + 1
                            if (b == "B"):
                                button_counts[1] = button_counts[1] + 1  

                            times.append(float(t))
                            stim_levels.append(int(s))
                            frequencies.append(float(r))
                    self.plot_data.clear()

                # stimulation frequency
                freqpath.plot(times, frequencies, color = 'g', marker = 'o')

                # Frequency World
                space.plot(times, stim_levels, color = 'purple', marker = 'o')

                # Total Button Presses
                count.bar(buttons, button_counts, color=bar_colors)
                
                plt.tight_layout()
                
                fig.canvas.draw()
                if not done:
                    plt.pause(0.0001)

            producer.join()
        except KeyboardInterrupt:
            print("plotter detected interrupt!")
        except Exception as err:
            print("ope")

        print("saving figure...")
        
        plt.savefig(f"{self.fname}.png")
        pickle.dump(fig, open(f"{self.fname}.fig.pickle", 'wb'))

        plt.clf()

