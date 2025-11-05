import "xterm";

export default {
  template: "<div></div>",
  mounted() {
    this.terminal = new Terminal(this.options);
    this.terminal.open(this.$el);

    this.ready = true;
    this.$emit("ready", { state: true });
  },
  beforeDestroy() {
    this.terminal.dispose();
  },
  beforeUnmount() {
    this.terminal.dispose();
  },
  methods: {
    call_api_method(name, ...args) {
      this.terminal[name](...args);
    },
    reset() {
      this.terminal.write("\x1bc");
    },
    write_base64_encoded_hex(data) {
      const hexString = data.base64_encoded_hex;
      if (hexString !== "" && this.ready) {
        let byteArray = new Uint8Array(
          hexString.match(/.{1,2}/g).map((byte) => parseInt(byte, 16))
        );
        let base64String = new TextDecoder("utf-8").decode(byteArray);
        const decodedData = atob(base64String);
        this.terminal.write(decodedData);
      }
    },
  },
  props: {
    options: Object,
  },
};
